"""Tests for scripts/check_commits.py (temporary git repos in tmp_path only)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_commits.py"
TRAILER = "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"


def env_for(home: Path) -> dict:
    """Isolated git environment: no personal or system git config is read."""
    return {
        **os.environ,
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }


class Repo:
    def __init__(self, path: Path):
        self.path = path
        self.env = env_for(path.parent / "home")
        (path.parent / "home").mkdir(exist_ok=True)
        path.mkdir()
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str, input: str | None = None) -> str:
        proc = subprocess.run(["git", *args], cwd=self.path, env=self.env, input=input,
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        return proc.stdout.strip()

    def write(self, rel: str, data: bytes | str = "x\n") -> None:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode())

    def commit(self, subject: str, files: dict[str, bytes | str] | None = None, trailer: str | None = TRAILER,
               body: str = "", remove: tuple[str, ...] = ()) -> str:
        files = files if files is not None else {"note.txt": subject}
        for rel, data in files.items():
            self.write(rel, data)
        for rel in remove:
            self.git("rm", "-q", "--", rel)
        if files:
            self.git("add", "--", *files)
        message = subject + "\n"
        if body:
            message += "\n" + body + "\n"
        if trailer:
            message += "\n" + trailer + "\n"
        self.git("commit", "-q", "--allow-empty", "-F", "-", input=message)
        return self.git("rev-parse", "HEAD")

    def check(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.path, env=self.env,
                              capture_output=True, text=True)


@pytest.fixture()
def repo(tmp_path):
    r = Repo(tmp_path / "repo")
    r.base = r.commit("init", trailer=None, files={"README.md": "hi\n"})
    return r


def run(repo: Repo, *args: str) -> subprocess.CompletedProcess:
    return repo.check("--range", f"{repo.base}..HEAD", *args)


def row(proc: subprocess.CompletedProcess, sha: str) -> list[str]:
    for line in proc.stdout.splitlines():
        if line.startswith(sha[:7]):
            return line.split()
    raise AssertionError(f"no table row for {sha[:7]}:\n{proc.stdout}")


# ---------------------------------------------------------------------------
# passing cases
# ---------------------------------------------------------------------------
def test_valid_commits_pass_with_summary(repo):
    a = repo.commit("[AI-FEAT] Add thing")
    b = repo.commit("[AI-PROJECT] acme-churn 04-analysis-plan: write the plan")
    c = repo.commit("[PROJECT] acme-churn 00 brief: my own words", trailer=None)  # human commit: no rule applies
    proc = run(repo)
    assert proc.returncode == 0, proc.stdout
    assert row(proc, a)[1:5] == ["ok", "ok", "--", "ok"]
    assert row(proc, b)[1:5] == ["ok", "ok", "ok", "ok"]
    assert row(proc, c)[1:5] == ["--", "--", "--", "ok"]
    assert "Summary: 3 commits checked, 0 errors, 0 warnings" in proc.stdout


@pytest.mark.parametrize("kind", ["PROJECT", "FEAT", "CHORE", "FIX"])
def test_all_allowed_types(repo, kind):
    subject = "[AI-PROJECT] demo 01-research: x" if kind == "PROJECT" else f"[AI-{kind}] x"
    repo.commit(subject)
    assert run(repo).returncode == 0


def test_empty_range_is_fine(repo):
    proc = run(repo)
    assert proc.returncode == 0
    assert "0 commits checked" in proc.stdout


# ---------------------------------------------------------------------------
# R1 / R2
# ---------------------------------------------------------------------------
def test_r1_trailer_without_ai_subject_fails(repo):
    sha = repo.commit("Fix stuff")
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[1] == "FAIL"
    assert "R1" in proc.stdout


def test_r1_trailer_check_is_case_insensitive(repo):
    sha = repo.commit("Fix stuff", trailer="co-authored-by: claude <x@y.z>")
    assert row(run(repo), sha)[1] == "FAIL"


def test_r1_other_co_authors_are_not_claude(repo):
    repo.commit("Pair work", trailer="Co-Authored-By: Alice <alice@example.com>")
    assert run(repo).returncode == 0


def test_r2_ai_subject_without_trailer_fails(repo):
    sha = repo.commit("[AI-CHORE] No trailer", trailer=None)
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[2] == "FAIL"


@pytest.mark.parametrize("subject", ["[AI-DOCS] x", "[AI-] x", "[AI-chore] x", "[AI-FEATURE] x"])
def test_r2_unknown_type_fails(repo, subject):
    sha = repo.commit(subject)
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[2] == "FAIL"


# ---------------------------------------------------------------------------
# R3
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subject",
    [
        "[AI-PROJECT] acme-churn 01-research: gather context",
        "[AI-PROJECT] a1 05-analysis: run it",
        "[AI-PROJECT] online-retail-growth 10-impact: forecast",
    ],
)
def test_r3_valid(repo, subject):
    repo.commit(subject)
    assert run(repo).returncode == 0


@pytest.mark.parametrize(
    "subject",
    [
        "[AI-PROJECT] acme-churn: no stage",
        "[AI-PROJECT] acme-churn 05 analysis: spaced stage",
        "[AI-PROJECT] Acme 05-analysis: bad slug",
        "[AI-PROJECT] acme_churn 05-analysis: bad slug",
        "[AI-PROJECT] acme--churn 05-analysis: bad slug",
        "[AI-PROJECT] acme-churn 5-analysis: one digit",
        "[AI-PROJECT] acme-churn 05-Analysis: capital",
        "[AI-PROJECT] acme-churn 05-analysis:",
        "[AI-PROJECT] acme-churn 05-analysis summary without colon",
        "[AI-PROJECT]acme-churn 05-analysis: no space",
    ],
)
def test_r3_invalid(repo, subject):
    sha = repo.commit(subject)
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[3] == "FAIL"


# ---------------------------------------------------------------------------
# R4
# ---------------------------------------------------------------------------
def test_r4_data_file_added_fails(repo):
    sha = repo.commit("[AI-FEAT] Add data", files={"Projects/demo/data/raw.csv": "a,b\n"})
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[4] == "FAIL"
    assert "Projects/demo/data/raw.csv" in proc.stdout


def test_r4_nested_data_path_fails(repo):
    repo.commit("[AI-FEAT] Add data", files={"Projects/demo/data/sub/raw.parquet": "x"})
    assert run(repo).returncode == 1


def test_r4_gitkeep_is_allowed(repo):
    repo.commit("[AI-CHORE] Keep folder", files={"Projects/demo/data/.gitkeep": "", "Projects/_template/data/.gitkeep": ""})
    assert run(repo).returncode == 0


def test_r4_data_file_modified_fails(repo):
    repo.write("Projects/demo/data/raw.csv", "a\n")
    repo.git("add", "--", "Projects/demo/data/raw.csv")
    repo.git("commit", "-q", "-m", "old human commit")
    base = repo.git("rev-parse", "HEAD")
    repo.commit("[AI-FIX] Touch data", files={"Projects/demo/data/raw.csv": "b\n"})
    proc = repo.check("--range", f"{base}..HEAD")
    assert proc.returncode == 1 and "R4" in proc.stdout


def test_r4_deleting_a_data_file_is_allowed(repo):
    repo.write("Projects/demo/data/raw.csv", "a\n")
    repo.git("add", "--", "Projects/demo/data/raw.csv")
    repo.git("commit", "-q", "-m", "old human commit")
    base = repo.git("rev-parse", "HEAD")
    repo.commit("[AI-CHORE] Stop tracking data", files={}, remove=("Projects/demo/data/raw.csv",))
    assert repo.check("--range", f"{base}..HEAD").returncode == 0


def test_r4_other_data_folders_are_not_project_data(repo):
    repo.commit("[AI-FEAT] Other places", files={"data/x.csv": "1", "Projects/demo/outputs/data/x.csv": "1", "docs/data/a.md": "1"})
    assert run(repo).returncode == 0


def test_r4_large_file_anywhere_fails(repo):
    sha = repo.commit("[AI-FEAT] Big", files={"docs/big.bin": b"x" * (6 * 1048576)})
    proc = run(repo)
    assert proc.returncode == 1
    assert row(proc, sha)[4] == "FAIL"
    assert "docs/big.bin" in proc.stdout


def test_r4_size_limit_boundary_and_option(repo):
    repo.commit("[AI-FEAT] Exactly 5 MB", files={"docs/five.bin": b"x" * (5 * 1048576)})
    assert run(repo).returncode == 0
    repo.commit("[AI-FEAT] Two MB", files={"docs/two.bin": b"x" * (2 * 1048576)})
    assert run(repo, "--max-size-mb", "1").returncode == 1
    assert run(repo, "--max-size-mb", "10").returncode == 0


def test_r4_oversized_modification_fails(repo):
    repo.write("docs/grow.bin", "small")
    repo.git("add", "--", "docs/grow.bin")
    repo.git("commit", "-q", "-m", "old")
    base = repo.git("rev-parse", "HEAD")
    repo.commit("[AI-FIX] Grow", files={"docs/grow.bin": b"x" * (6 * 1048576)})
    assert repo.check("--range", f"{base}..HEAD").returncode == 1


# ---------------------------------------------------------------------------
# warning and summary
# ---------------------------------------------------------------------------
def test_session_trailer_warns_but_does_not_fail(repo):
    sha = repo.commit("[AI-CHORE] With session", body="Claude-Session: https://claude.ai/code/session_abc\nclaude-session: second")
    repo.commit("[AI-CHORE] Without session")
    proc = run(repo)
    assert proc.returncode == 0
    assert row(proc, sha)[5] == "yes"
    assert "Summary: 2 commits checked, 0 errors, 1 warnings" in proc.stdout
    assert "세션 주소" in proc.stdout
    assert "2개" in proc.stdout  # two trailers counted


def test_summary_counts_errors_per_rule(repo):
    repo.commit("Plain subject with trailer")  # R1
    repo.commit("[AI-PROJECT] bad subject")  # R3
    proc = run(repo)
    assert proc.returncode == 1
    assert "Summary: 2 commits checked, 2 errors, 0 warnings" in proc.stdout


# ---------------------------------------------------------------------------
# range selection
# ---------------------------------------------------------------------------
def test_no_upstream_and_no_origin_main_is_an_error(repo):
    repo.commit("[AI-CHORE] x")
    proc = repo.check()
    assert proc.returncode == 1
    assert "no commit range" in proc.stderr


def test_default_range_uses_upstream(repo, tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], env=repo.env, check=True)
    repo.git("remote", "add", "origin", str(remote))
    repo.commit("[AI-CHORE] already pushed", trailer=None)  # would be an R2 error if it were checked
    repo.git("push", "-q", "-u", "origin", "main")
    repo.commit("[AI-CHORE] new work")
    proc = repo.check()
    assert proc.returncode == 0, proc.stdout
    assert "1 commits checked" in proc.stdout
    assert "@{upstream}..HEAD" in proc.stdout


def test_default_range_falls_back_to_origin_main(repo, tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], env=repo.env, check=True)
    repo.git("remote", "add", "origin", str(remote))
    repo.git("push", "-q", "origin", "main")  # no -u: no upstream configured
    repo.git("fetch", "-q", "origin")
    repo.commit("[AI-CHORE] new work")
    proc = repo.check()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "origin/main..HEAD" in proc.stdout


def test_invalid_range_is_an_error(repo):
    proc = repo.check("--range", "nope..HEAD")
    assert proc.returncode == 1
    assert "error" in proc.stderr
