#!/usr/bin/env python3
"""PreToolUse guard hook for Claude Code (standard library only).

Reads the hook JSON from stdin. Exit code 2 blocks the tool call and the short
English reason on stderr is shown to the agent. Exit 0 allows the call.
Any other exit code would NOT block, so every error path ends in exit 2 (G5).

Rules
  G1 all calls (main session too):
     - never touch .env* (except .env.example), .zshrc, .envrc via Read/Edit/Write/Bash
     - the human approval line of 04_analysis_plan.md is written by the human only:
       Write/Edit text is rejected when a LINE STARTS with the approval phrase
       (markdown prefixes, case and spacing variants included); a Bash command is
       rejected when it contains the phrase anywhere.
  G2 subagents (hook input has agent_type):
     - write only inside Projects/<slug>/ where slug does not start with "_" AND
       equals the slug in .claude/active_project (missing, empty or invalid file:
       deny, fail closed; the /run-project skill writes and clears that file)
     - never write .claude/, CLAUDE.md, .git/, scripts/, root tests/, Learning/,
       Practice/, Projects/_*/ ; never write the human workflow documents (00, 02,
       07, 09 and 06_fail_resolution.md);
       never modify 03_data_plan.md or 04_analysis_plan.md once they carry the
       approval line
     - MultiEdit and NotebookEdit are rejected outright (no path parsing)
  G3 per-agent allow lists (relative to Projects/<slug>/); other agent types: G2 only
  G4 subagent Bash: BEST EFFORT, see "Limits" below
  G5 fail closed on unreadable input or unexpected errors

Paths are resolved with realpath, so '..' and symlink escapes are judged by their
real target. Protected names are compared case-insensitively (macOS).

Limits of the Bash check (G4). It only inspects the command text:
  - writes done INSIDE a program (python script/-c, make, node, dd of=, ...) are invisible
  - variables, command substitution, eval, xargs, find -exec/-delete are not expanded
  - only `bash|sh|zsh|dash -c "..."` is re-checked (two levels)
  - writers other than > >> tee sed -i mv cp (touch, mkdir, ln, install, rsync, ...) are not checked
  - commands that cannot be parsed are rejected, which can block unusual but valid input
  - the active project comes from .claude/active_project, not from the call itself
Tools outside the matcher (Grep, Glob, ...) are never seen by this hook.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

DISABLE_HINT = (
    "To disable the guard temporarily, remove its entry under hooks.PreToolUse in "
    ".claude/settings.json (edit the file by hand)."
)

HANDLED_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "Read"}

# --- G1 patterns -----------------------------------------------------------
# Built from pieces so this source never contains the literal approval phrase.
_A = "appro" + "ved"
_H = "hu" + "man"
APPROVAL_LINE_RE = re.compile(
    r"^(?:[ \t>*_#`+•-]|\d+[.)])*" + _A + r"[ \t*_`]*:[ \t*_`]*" + _H + r"\b",
    re.IGNORECASE | re.MULTILINE,
)
APPROVAL_CMD_RE = re.compile(_A + r"[\s*_`]*:[\s*_`]*" + _H, re.IGNORECASE)

SENSITIVE_NAME_RE = re.compile(r"\.(?:envrc|zshrc|env(?:\.[\w.-]+)?)")
SENSITIVE_CMD_RE = re.compile(r"(?<!\w)\.(?:envrc|zshrc|env(?:\.[\w.-]*)?)(?![\w-])", re.IGNORECASE)

# --- G2 / G3 ---------------------------------------------------------------
PROTECTED_TOP = {".claude", ".git", "scripts", "tests", "learning", "practice"}
HUMAN_FILES = {
    "00_brief.md",
    "02_questions.md",
    "07_insights.md",
    "09_recommendations.md",
    "06_fail_resolution.md",
}
# files a subagent may no longer modify once they carry the approval line
APPROVAL_LOCKED = {("workflow", "03_data_plan.md"), ("workflow", "04_analysis_plan.md")}
ACTIVE_PROJECT_FILE = (".claude", "active_project")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NO_ACTIVE_PROJECT = (
    "no active project: .claude/active_project is missing, empty or invalid; "
    "the /run-project skill writes the slug there before it starts a subagent"
)

ALLOW = {
    "researcher": ["workflow/01_research.md", "workflow/03_data_plan.md"],
    "question-coach": ["workflow/02_questions_feedback.md"],
    "analyst": [
        "workflow/04_analysis_plan.md",
        "workflow/05_analysis.md",
        "pipeline/**",
        "outputs/**",
        "notebooks/**",
        "data/**",
        "data_manifest.json",
        "main.py",
        "tests/test_*.py",
    ],
    "validator": ["workflow/06_validation.md", "workflow/logs/**", "tests/test_validation_*.py"],
    "critic": ["workflow/08_critique.md"],
    "impact-modeler": [
        "workflow/10_impact.md",
        "workflow/10_impact_assumptions.json",
        "pipeline/impact_*.py",
        "outputs/impact_*",
    ],
}
DENY = {"analyst": ["tests/test_validation_*.py"]}  # checked before ALLOW


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    out: list[str] = []
    i = 0
    pattern = pattern.casefold()
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".+")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


_ALLOW_RE = {a: [_glob_to_regex(p) for p in ps] for a, ps in ALLOW.items()}
_DENY_RE = {a: [_glob_to_regex(p) for p in ps] for a, ps in DENY.items()}

# --- G4 --------------------------------------------------------------------
DENY_CMDS = {"rm", "sudo", "chmod", "ssh", "scp", "curl", "wget"}
DENY_GIT = {"commit", "push", "add", "reset", "checkout", "restore", "rebase", "merge", "stash", "clean"}
WRAPPERS = {"command", "nohup", "time", "exec", "env", "nice", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash"}
SAFE_DEVICES = {"/dev/null", "/dev/stdout", "/dev/stderr"}
PUNCT = set("();<>|&")


class Deny(Exception):
    """Raised internally with a short reason."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def project_root() -> str:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    base = env if env else str(Path(__file__).resolve().parents[2])
    return os.path.realpath(base)


def resolve(path: str, cwd: str) -> str:
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        p = os.path.join(cwd, p)
    return os.path.realpath(p)


def is_sensitive_name(name: str) -> bool:
    name = name.casefold()
    return name != ".env.example" and bool(SENSITIVE_NAME_RE.fullmatch(name))


def _norm_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def has_approval_line(text: str) -> bool:
    return bool(APPROVAL_LINE_RE.search(_norm_text(text)))


# ---------------------------------------------------------------------------
# G1
# ---------------------------------------------------------------------------
def g1_reason(tool: str, ti: dict, cwd: str) -> str | None:
    paths: list[str] = []
    texts: list[str] = []
    if tool in ("Read", "Write", "Edit"):
        paths.append(ti["file_path"])
    elif tool == "MultiEdit":
        if "file_path" in ti:
            paths.append(ti["file_path"])
        texts += [e.get("new_string", "") for e in ti.get("edits", []) if isinstance(e, dict)]
    elif tool == "NotebookEdit":
        for key in ("notebook_path", "file_path"):
            if key in ti:
                paths.append(ti[key])
        if isinstance(ti.get("new_source"), str):
            texts.append(ti["new_source"])
    if tool == "Write":
        texts.append(ti["content"])
    if tool == "Edit":
        texts.append(ti["new_string"])

    for p in paths:
        if not isinstance(p, str):
            raise ValueError("file path is not a string")
        names = {os.path.basename(p), os.path.basename(resolve(p, cwd))}
        if any(is_sensitive_name(n) for n in names):
            return "access to .env*, .zshrc and .envrc files is not allowed"
    for t in texts:
        if isinstance(t, str) and has_approval_line(t):
            return "the human approval line is written by the human only; do not add it"

    if tool == "Bash":
        cmd = ti["command"]
        if not isinstance(cmd, str):
            raise ValueError("command is not a string")
        for m in SENSITIVE_CMD_RE.finditer(cmd):
            if m.group(0).casefold() != ".env.example":
                return "commands touching .env*, .zshrc or .envrc are not allowed"
        if APPROVAL_CMD_RE.search(cmd):
            return "the human approval line is written by the human only; do not put it in commands"
    return None


# ---------------------------------------------------------------------------
# G2 + G3
# ---------------------------------------------------------------------------
def _active_slug(root: str) -> str | None:
    """Slug in .claude/active_project, or None when missing, empty or invalid (fail closed)."""
    try:
        with open(os.path.join(root, *ACTIVE_PROJECT_FILE), encoding="utf-8") as fh:
            slug = fh.read().strip()
    except OSError:
        return None
    return slug if SLUG_RE.fullmatch(slug) else None


def subagent_write_reason(real: str, root: str, agent_type: str | None) -> str | None:
    try:
        parts = Path(real).relative_to(root).parts
    except ValueError:
        return "writes outside the project root are not allowed"
    low = [p.casefold() for p in parts]
    if not low:
        return "cannot write to the project root itself"
    top = low[0]
    if top in PROTECTED_TOP or (len(low) == 1 and top == "claude.md"):
        return f"subagents may not write {parts[0]}"
    if top != "projects":
        return "subagents may write only inside Projects/<slug>/"
    if len(low) < 3:
        return "subagents may write only inside Projects/<slug>/"
    if low[1].startswith("_"):
        return f"Projects/{parts[1]}/ is not a project (names starting with _ are protected)"
    active = _active_slug(root)
    if active is None:
        return NO_ACTIVE_PROJECT
    if low[1] != active.casefold():
        return f"Projects/{parts[1]}/ is not the active project ({active})"

    inner = low[2:]
    inner_s = "/".join(inner)
    if len(inner) == 2 and inner[0] == "workflow" and inner[1] in HUMAN_FILES:
        return f"{parts[-1]} is a human-authored document"
    if tuple(inner) in APPROVAL_LOCKED and os.path.isfile(real):
        with open(real, encoding="utf-8", errors="ignore") as fh:
            if has_approval_line(fh.read()):
                return f"{parts[-1]} is already approved by the human; do not modify it"

    if agent_type in _ALLOW_RE:
        if any(rx.match(inner_s) for rx in _DENY_RE.get(agent_type, [])):
            return f"{agent_type} may not write {'/'.join(parts[2:])}"
        if not any(rx.match(inner_s) for rx in _ALLOW_RE[agent_type]):
            return f"{agent_type} may not write {'/'.join(parts[2:])} (outside its allow list)"
    return None


# ---------------------------------------------------------------------------
# G4 (best effort)
# ---------------------------------------------------------------------------
def _strip_heredocs(command: str) -> str:
    out: list[str] = []
    term: str | None = None
    for line in command.replace("\\\n", "").split("\n"):
        if term is not None:
            if line.strip() == term:
                term = None
            continue
        out.append(line)
        m = re.search(r"(?<!<)<<-?\s*(['\"]?)(\w+)\1", line)
        if m:
            term = m.group(2)
    return "\n".join(out)


def _tokenize(line: str) -> list[str]:
    lex = shlex.shlex(line, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _split_segments(tokens: list[str]) -> list[tuple[list[str], list[str]]]:
    """Return [(words, redirect_targets)] per simple command."""
    segments: list[tuple[list[str], list[str]]] = []
    words: list[str] = []
    targets: list[str] = []

    def flush() -> None:
        nonlocal words, targets
        if words or targets:
            segments.append((words, targets))
        words, targets = [], []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t and set(t) <= PUNCT:
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if ">" in t:
                if t.endswith("&") and nxt is not None and (nxt.isdigit() or nxt == "-"):
                    i += 2  # fd duplication such as 2>&1
                    continue
                if nxt is not None:
                    targets.append(nxt)
                i += 2
                continue
            if "<" in t:
                i += 2  # input redirect, heredoc delimiter or here-string
                continue
            flush()
            i += 1
            continue
        words.append(t)
        i += 1
    flush()
    return segments


def _check_target(token: str, cwd: str, root: str, agent_type: str | None) -> None:
    if token in SAFE_DEVICES:
        return
    if "$" in token or "`" in token:
        raise Deny(f"cannot verify the write target {token!r}; use a literal path")
    reason = subagent_write_reason(resolve(token, cwd), root, agent_type)
    if reason:
        raise Deny(reason)


def _non_options(args: list[str], skip_value_of: tuple[str, ...] = ()) -> list[str]:
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a in skip_value_of:
            i += 2
            continue
        if not a.startswith("-"):
            out.append(a)
        i += 1
    return out


def _target_dir_option(args: list[str]) -> str | None:
    for i, a in enumerate(args):
        if a in ("-t", "--target-directory") and i + 1 < len(args):
            return args[i + 1]
        if a.startswith("--target-directory="):
            return a.split("=", 1)[1]
    return None


def _git_subcommand(args: list[str]) -> str | None:
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            return a
    return None


def _segment(words: list[str], targets: list[str], cwd: str, root: str, agent_type: str | None, depth: int) -> None:
    for t in targets:
        _check_target(t, cwd, root, agent_type)
    while words and (re.match(r"^\w+=", words[0]) or words[0] in WRAPPERS):
        words = words[1:]
    if not words:
        return
    cmd = os.path.basename(words[0])
    args = words[1:]

    if cmd in DENY_CMDS:
        raise Deny(f"'{cmd}' is not allowed for subagents")
    if cmd == "git":
        sub = _git_subcommand(args)
        if sub in DENY_GIT:
            raise Deny(f"'git {sub}' is not allowed for subagents; the orchestrator commits")
    if cmd in ("pip", "pip3") and "install" in args:
        raise Deny("installing packages is not allowed for subagents")
    if cmd == "uv" and ("install" in args or "add" in args):
        raise Deny("installing packages is not allowed for subagents")
    if cmd in ("npm", "pnpm") and any(a in ("install", "i", "ci", "add") for a in args[:2]):
        raise Deny("installing packages is not allowed for subagents")
    if re.fullmatch(r"python[\d.]*", cmd) and "-m" in args:
        j = args.index("-m")
        if j + 1 < len(args) and args[j + 1] == "pip" and "install" in args:
            raise Deny("installing packages is not allowed for subagents")

    if cmd in SHELLS:
        for j, a in enumerate(args[:-1]):
            if re.fullmatch(r"-[a-z]*c", a):
                nested = bash_reason(args[j + 1], cwd, root, agent_type, depth + 1)
                if nested:
                    raise Deny(nested)
                break

    if cmd == "tee":
        for f in _non_options(args):
            _check_target(f, cwd, root, agent_type)
    elif cmd == "sed":
        in_place = any(re.match(r"^-[A-Za-z]*i", a) or a.startswith("--in-place") for a in args)
        if in_place:
            script_given = any(a in ("-e", "-f", "--expression", "--file") for a in args)
            files = _non_options(args, ("-e", "-f", "--expression", "--file"))
            for f in files if script_given else files[1:]:
                _check_target(f, cwd, root, agent_type)
    elif cmd in ("mv", "cp"):
        tdir = _target_dir_option(args)
        ops = _non_options(args, ("-t", "--target-directory"))
        if cmd == "mv":
            check = ops + ([tdir] if tdir else [])
        else:
            check = [tdir] if tdir else ops[-1:]
        for f in check:
            _check_target(f, cwd, root, agent_type)


def bash_reason(command: str, cwd: str, root: str, agent_type: str | None, depth: int = 0) -> str | None:
    if depth > 2:
        return "command nesting is too deep to verify"
    try:
        for line in _strip_heredocs(command).split("\n"):
            if not line.strip():
                continue
            try:
                tokens = _tokenize(line)
            except ValueError:
                raise Deny("could not parse the shell command; simplify it") from None
            for words, targets in _split_segments(tokens):
                _segment(words, targets, cwd, root, agent_type, depth)
    except Deny as d:
        return str(d)
    return None


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def evaluate(data: dict) -> str | None:
    tool = data["tool_name"]
    if tool not in HANDLED_TOOLS:
        return None
    ti = data["tool_input"]
    if not isinstance(ti, dict):
        raise ValueError("tool_input is not an object")
    root = project_root()
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) and data.get("cwd") else root

    reason = g1_reason(tool, ti, cwd)
    if reason:
        return reason

    is_sub = data.get("agent_type") is not None
    if not is_sub:
        return None
    agent_type = data["agent_type"]

    if tool in ("MultiEdit", "NotebookEdit"):
        return f"subagents may not use {tool}"
    if tool == "Read":
        return None
    if tool in ("Write", "Edit"):
        return subagent_write_reason(resolve(ti["file_path"], cwd), root, agent_type)
    if tool == "Bash":
        return bash_reason(ti["command"], cwd, root, agent_type)
    return None


def _block(message: str) -> None:
    sys.stderr.write(f"guard: blocked: {message}\n")
    sys.exit(2)


def main() -> int:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("hook input is not a JSON object")
        reason = evaluate(data)
    except Exception as exc:  # fail closed (G5)
        _block(f"guard error ({type(exc).__name__}: {exc}). {DISABLE_HINT}")
        return 2  # unreachable
    if reason:
        _block(reason)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001 - last resort, still fail closed
        sys.stderr.write(f"guard: blocked: unexpected failure. {DISABLE_HINT}\n")
        sys.exit(2)
