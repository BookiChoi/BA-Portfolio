"""Check commit messages and changed files before pushing (read-only git commands).

Usage:
    python scripts/check_commits.py [--range <rev-range>] [--max-size-mb 5]

Default range: @{upstream}..HEAD, or origin/main..HEAD when there is no upstream.
Exit code 1 when there is an error (or no range can be determined), otherwise 0.

Rules (errors)
  R1 a message with a "Co-Authored-By: Claude" trailer needs a subject starting with
     [AI-PROJECT], [AI-FEAT], [AI-CHORE] or [AI-FIX]
  R2 a subject starting with "[AI-" needs that trailer and an allowed TYPE
  R3 [AI-PROJECT] subjects use "[AI-PROJECT] <slug> <stage>: <summary>"
     (slug ^[a-z0-9]+(-[a-z0-9]+)*$, stage ^[0-9]{2}-[a-z0-9-]+$)
  R4 data safety: no added/modified/renamed-to file under Projects/*/data/ (except
     .gitkeep) and no added/modified file larger than --max-size-mb
Warning (does not change the exit code)
  a "Claude-Session:" trailer in a message

Limits: merge commits get the message checks only (git shows no file list for them
by default). Sizes are the blob sizes of the committed files, 1 MB = 1,048,576 bytes.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

ALLOWED_TYPES = ("PROJECT", "FEAT", "CHORE", "FIX")
CO_AUTHOR_RE = re.compile(r"^co-authored-by:\s*claude\b", re.IGNORECASE | re.MULTILINE)
SESSION_RE = re.compile(r"^claude-session:", re.IGNORECASE | re.MULTILINE)
AI_TYPE_RE = re.compile(r"^\[AI-([A-Za-z]*)\]")
AI_SUBJECT_RE = re.compile(r"^\[AI-(?:" + "|".join(ALLOWED_TYPES) + r")\]")
PROJECT_RE = re.compile(r"^\[AI-PROJECT\] ([a-z0-9]+(?:-[a-z0-9]+)*) ([0-9]{2}-[a-z0-9-]+): \S")
DATA_PATH_RE = re.compile(r"^Projects/[^/]+/data/(.+)$")
CHANGED_STATUSES = ("A", "M", "R", "C", "T")  # files whose new content exists after the commit

SESSION_NOTE = (
    "경고: 'Claude-Session:' 트레일러가 {commits}개 커밋에 모두 {count}개 있습니다. "
    "이 레포가 공개 저장소라면 push할 때 세션 주소가 함께 공개됩니다. "
    "공개하고 싶지 않다면 push 전에 해당 커밋 메시지를 확인하세요."
)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def git_bytes(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True)


def resolve_range(explicit: str | None) -> tuple[str | None, str | None]:
    """Return (range, error)."""
    if explicit:
        return explicit, None
    if git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").returncode == 0:
        return "@{upstream}..HEAD", None
    if git("rev-parse", "--verify", "-q", "origin/main").returncode == 0:
        return "origin/main..HEAD", None
    return None, (
        "no commit range: the current branch has no upstream and origin/main does not exist. "
        "Pass --range <rev-range>, for example --range main..HEAD."
    )


def changed_files(sha: str) -> list[tuple[str, str]]:
    """[(status letter, path)] for files that exist after the commit (A, M, R, C, T)."""
    proc = git_bytes("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "-M", "-z", sha)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip())
    tokens = proc.stdout.decode("utf-8", "replace").split("\0")
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens) and tokens[i]:
        status = tokens[i][0]
        if status in ("R", "C"):
            out.append((status, tokens[i + 2]))  # the new path
            i += 3
        else:
            out.append((status, tokens[i + 1]))
            i += 2
    return [(s, p) for s, p in out if s in CHANGED_STATUSES]


def blob_size(sha: str, path: str) -> int | None:
    proc = git("cat-file", "-s", f"{sha}:{path}")
    if proc.returncode != 0:
        return None
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return None


def check_commit(sha: str, message: str, max_bytes: float) -> dict:
    """Return {'rules': {R1..R4: ok|FAIL|--}, 'errors': [...], 'warnings': int}."""
    subject = message.splitlines()[0] if message.strip() else ""
    has_trailer = bool(CO_AUTHOR_RE.search(message))
    rules = {"R1": "--", "R2": "--", "R3": "--", "R4": "ok"}
    errors: list[str] = []

    if has_trailer:
        rules["R1"] = "ok"
        if not AI_SUBJECT_RE.match(subject):
            rules["R1"] = "FAIL"
            errors.append("R1: has a Co-Authored-By: Claude trailer but the subject does not start with "
                          "[AI-PROJECT], [AI-FEAT], [AI-CHORE] or [AI-FIX]")

    if subject.startswith("[AI-"):
        rules["R2"] = "ok"
        m = AI_TYPE_RE.match(subject)
        if not has_trailer:
            rules["R2"] = "FAIL"
            errors.append("R2: subject starts with [AI- but there is no Co-Authored-By: Claude trailer")
        if not m or m.group(1) not in ALLOWED_TYPES:
            rules["R2"] = "FAIL"
            errors.append(f"R2: TYPE is not one of {', '.join(ALLOWED_TYPES)}")

    if subject.startswith("[AI-PROJECT]"):
        rules["R3"] = "ok"
        if not PROJECT_RE.match(subject):
            rules["R3"] = "FAIL"
            errors.append("R3: use '[AI-PROJECT] <slug> <stage>: <summary>' (slug like acme-churn, stage like 04-analysis-plan)")

    for status, path in changed_files(sha):
        m = DATA_PATH_RE.match(path)
        if m and m.group(1).rsplit("/", 1)[-1] != ".gitkeep":
            rules["R4"] = "FAIL"
            errors.append(f"R4: data file touched: {path}")
            continue
        if status in ("A", "M", "R", "C"):
            size = blob_size(sha, path)
            if size is not None and size > max_bytes:
                rules["R4"] = "FAIL"
                errors.append(f"R4: {path} is {size / 1048576:.1f} MB (limit {max_bytes / 1048576:g} MB)")

    session_count = len(SESSION_RE.findall(message))
    return {"rules": rules, "errors": errors, "sessions": session_count}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check commit messages and files before pushing.")
    parser.add_argument("--range", dest="rev_range", help="git revision range (default: @{upstream}..HEAD, else origin/main..HEAD)")
    parser.add_argument("--max-size-mb", type=float, default=5.0, help="largest allowed added/modified file (default 5)")
    args = parser.parse_args(argv)

    rev_range, error = resolve_range(args.rev_range)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    listing = git("rev-list", "--reverse", rev_range)
    if listing.returncode != 0:
        print(f"error: git rev-list {rev_range} failed: {listing.stderr.strip()}", file=sys.stderr)
        return 1
    shas = listing.stdout.split()
    max_bytes = args.max_size_mb * 1048576

    rows: list[tuple[str, dict, str]] = []
    for sha in shas:
        proc = git("log", "-1", "--format=%B", sha)
        message = proc.stdout.rstrip("\n")
        try:
            result = check_commit(sha, message, max_bytes)
        except RuntimeError as exc:
            print(f"error: could not read the changed files of {sha[:7]}: {exc}", file=sys.stderr)
            return 1
        subject = message.splitlines()[0] if message.strip() else "(empty message)"
        rows.append((sha, result, subject))

    print(f"Range: {rev_range}  (max file size {args.max_size_mb:g} MB)")
    print()
    print(f"{'Commit':<8} {'R1':<4} {'R2':<4} {'R3':<4} {'R4':<4} {'Warn':<4}  Subject")
    for sha, res, subject in rows:
        r = res["rules"]
        warn = "yes" if res["sessions"] else "-"
        print(f"{sha[:7]:<8} {r['R1']:<4} {r['R2']:<4} {r['R3']:<4} {r['R4']:<4} {warn:<4}  {subject[:70]}")

    n_errors = sum(len(res["errors"]) for _, res, _ in rows)
    warned = [res for _, res, _ in rows if res["sessions"]]
    total_sessions = sum(res["sessions"] for res in warned)

    if n_errors:
        print("\nErrors:")
        for sha, res, _ in rows:
            for message in res["errors"]:
                print(f"  {sha[:7]} {message}")
    if warned:
        print("\n" + SESSION_NOTE.format(commits=len(warned), count=total_sessions))
        for sha, res, _ in rows:
            if res["sessions"]:
                print(f"  {sha[:7]}: {res['sessions']} trailer(s)")

    print(f"\nSummary: {len(rows)} commits checked, {n_errors} errors, {len(warned)} warnings")
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
