"""Tests for .claude/hooks/guard.py.

guard.py is run as a subprocess against a fake project in tmp_path
(CLAUDE_PROJECT_DIR); real repo files are never touched.
The approval phrase is built from pieces so this file never contains it literally.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / ".claude" / "hooks" / "guard.py"
SETTINGS = REPO / ".claude" / "settings.json"

APPROVAL = "Appro" + "ved" + ": " + "hu" + "man"
APPROVAL_VARIANTS = [
    APPROVAL,
    "  " + APPROVAL,
    APPROVAL.upper(),
    "Appro" + "ved:" + "hu" + "man",
    "- " + APPROVAL,
    "* " + APPROVAL,
    "> " + APPROVAL,
    "# " + APPROVAL,
    "1. " + APPROVAL,
    "**Appro" + "ved:** " + "hu" + "man",
    "- **Appro" + "ved**: " + "hu" + "man",
    "Appro" + "ved : " + "hu" + "man",
]
ALL_AGENTS = ["researcher", "question-coach", "analyst", "validator", "critic", "impact-modeler"]


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------
@pytest.fixture()
def repo(tmp_path):
    root = (tmp_path / "repo").resolve()
    proj = root / "Projects" / "demo"
    for d in [
        proj / "workflow" / "logs",
        proj / "pipeline",
        proj / "tests",
        proj / "data",
        proj / "outputs",
        proj / "notebooks",
        root / "Projects" / "_template",
        root / ".claude",
        root / ".git",
        root / "scripts",
        root / "tests",
        root / "Learning",
        root / "Practice",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (root / ".env.example").write_text("SECRET=\n", encoding="utf-8")
    (root / ".zshrc").write_text("x\n", encoding="utf-8")
    (root / ".envrc").write_text("x\n", encoding="utf-8")
    (proj / "workflow" / "04_analysis_plan.md").write_text("Author: ai/analyst\nplan\n", encoding="utf-8")
    (proj / "pipeline" / "load.py").write_text("pass\n", encoding="utf-8")
    return root


def call(repo: Path, tool: str, tool_input: dict, agent: str | None = None, cwd: Path | None = None):
    payload: dict = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
        "cwd": str(cwd or repo),
    }
    if agent is not None:
        payload["agent_type"] = agent
        payload["agent_id"] = "a1"
    return run_raw(repo, json.dumps(payload))


def run_raw(repo: Path, stdin: str):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(repo)}
    proc = subprocess.run(
        [sys.executable, str(GUARD)], input=stdin, capture_output=True, text=True, env=env
    )
    return proc.returncode, proc.stderr


def write(repo, agent, rel, content="x\n"):
    return call(repo, "Write", {"file_path": str(repo / rel), "content": content}, agent)


def bash(repo, agent, command, cwd=None):
    return call(repo, "Bash", {"command": command}, agent, cwd=cwd)


def allowed(result):
    code, err = result
    assert code == 0, err


def denied(result):
    code, err = result
    assert code == 2
    assert err.startswith("guard: blocked:")


P = "Projects/demo/"


# ---------------------------------------------------------------------------
# G3: per-agent allow lists
# ---------------------------------------------------------------------------
def test_researcher_allow_and_deny(repo):
    allowed(write(repo, "researcher", P + "workflow/01_research.md"))
    allowed(write(repo, "researcher", P + "workflow/03_data_plan.md"))
    denied(write(repo, "researcher", P + "workflow/02_questions.md"))
    denied(write(repo, "researcher", P + "workflow/notes.md"))
    denied(write(repo, "researcher", P + "pipeline/x.py"))


def test_question_coach(repo):
    allowed(write(repo, "question-coach", P + "workflow/02_questions_feedback.md"))
    denied(write(repo, "question-coach", P + "workflow/02_questions.md"))


@pytest.mark.parametrize(
    "rel",
    [
        "workflow/04_analysis_plan.md",
        "workflow/05_analysis.md",
        "pipeline/new.py",
        "pipeline/sub/deep.py",
        "outputs/a.csv",
        "notebooks/n.ipynb",
        "data/raw.csv",
        "data_manifest.json",
        "main.py",
        "tests/test_pipeline.py",
    ],
)
def test_analyst_allowed(repo, rel):
    allowed(write(repo, "analyst", P + rel))


@pytest.mark.parametrize(
    "rel",
    ["tests/test_validation_x.py", "README.md", "config.yaml", "workflow/06_validation.md", "workflow/08_critique.md"],
)
def test_analyst_denied(repo, rel):
    denied(write(repo, "analyst", P + rel))


def test_validator(repo):
    allowed(write(repo, "validator", P + "tests/test_validation_x.py"))
    allowed(write(repo, "validator", P + "workflow/06_validation.md"))
    allowed(write(repo, "validator", P + "workflow/logs/run.txt"))
    denied(write(repo, "validator", P + "pipeline/load.py"))
    denied(call(repo, "Edit", {"file_path": str(repo / P / "pipeline/load.py"), "old_string": "pass", "new_string": "x"}, "validator"))
    denied(write(repo, "validator", P + "tests/test_other.py"))


def test_critic_and_impact_modeler(repo):
    allowed(write(repo, "critic", P + "workflow/08_critique.md"))
    denied(write(repo, "critic", P + "workflow/07_insights.md"))
    for rel in ["workflow/10_impact.md", "workflow/10_impact_assumptions.json", "pipeline/impact_model.py", "outputs/impact_chart.png"]:
        allowed(write(repo, "impact-modeler", P + rel))
    for rel in ["pipeline/load.py", "outputs/other.png", "workflow/09_recommendations.md"]:
        denied(write(repo, "impact-modeler", P + rel))


# ---------------------------------------------------------------------------
# G2: protected places, human documents, unknown agent types
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("agent", ALL_AGENTS)
@pytest.mark.parametrize("name", ["00_brief.md", "02_questions.md", "07_insights.md", "09_recommendations.md"])
def test_human_documents_are_never_writable_by_agents(repo, agent, name):
    denied(write(repo, agent, P + "workflow/" + name))


@pytest.mark.parametrize(
    "rel",
    [
        "CLAUDE.md",
        "claude.md",
        ".claude/settings.json",
        ".claude/agents/analyst.md",
        ".git/config",
        "scripts/new_project.py",
        "tests/test_x.py",
        "Learning/n.ipynb",
        "Practice/n.ipynb",
        "Projects/_template/README.md",
        "Projects/_hidden/x.md",
        "Projects/README.md",
        "README.md",
    ],
)
def test_protected_paths_denied_for_subagents(repo, rel):
    denied(write(repo, "analyst", rel))
    denied(write(repo, "general-purpose", rel))


def test_dotdot_bypass_denied(repo):
    raw = str(repo / "Projects" / ".." / "CLAUDE.md")
    denied(call(repo, "Write", {"file_path": raw, "content": "x"}, "analyst"))
    raw2 = str(repo / "Projects" / "demo" / ".." / ".." / "CLAUDE.md")
    denied(call(repo, "Write", {"file_path": raw2, "content": "x"}, "general-purpose"))


def test_outside_root_denied(repo, tmp_path):
    denied(call(repo, "Write", {"file_path": str(tmp_path / "elsewhere.txt"), "content": "x"}, "analyst"))


def test_symlink_bypass_denied(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    out_dir_link = repo / "Projects" / "demo" / "outputs" / "escape"
    file_link = repo / "Projects" / "demo" / "outputs" / "claude_link.md"
    try:
        os.symlink(outside, out_dir_link)
        os.symlink(repo / "CLAUDE.md", file_link)
    except OSError:
        pytest.skip("symlinks not supported")
    denied(write(repo, "analyst", P + "outputs/escape/x.txt"))
    denied(write(repo, "analyst", P + "outputs/claude_link.md"))


def test_unknown_agent_type_gets_only_g2(repo):
    allowed(write(repo, "general-purpose", P + "anything/else.txt"))
    denied(write(repo, "general-purpose", "CLAUDE.md"))
    denied(write(repo, "general-purpose", P + "workflow/00_brief.md"))


def test_subagent_read_only_g1(repo):
    allowed(call(repo, "Read", {"file_path": str(repo / "CLAUDE.md")}, "analyst"))
    denied(call(repo, "Read", {"file_path": str(repo / ".env")}, "analyst"))


# ---------------------------------------------------------------------------
# approval line (G1 + G2)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("variant", APPROVAL_VARIANTS)
def test_approval_line_denied_for_analyst_and_main(repo, variant):
    content = "Author: human\n\n" + variant + "\n"
    plan = P + "workflow/04_analysis_plan.md"
    denied(write(repo, "analyst", plan, content))
    denied(write(repo, None, plan, content))  # main session as well
    denied(call(repo, "Edit", {"file_path": str(repo / plan), "old_string": "plan", "new_string": variant}, None))


def test_approval_phrase_inside_prose_is_allowed_for_main_session(repo):
    text = "The line `" + APPROVAL + "` is added by the human only.\n"
    allowed(write(repo, None, P + "workflow/00_brief.md", text))
    allowed(write(repo, None, "CLAUDE.md", "note: " + APPROVAL + " is manual\n"))


def test_already_approved_plan_cannot_be_modified_by_subagents(repo):
    plan = repo / "Projects" / "demo" / "workflow" / "04_analysis_plan.md"
    plan.write_text("Author: ai/analyst\nplan\n" + APPROVAL + "\n", encoding="utf-8")
    denied(call(repo, "Edit", {"file_path": str(plan), "old_string": "plan", "new_string": "new plan"}, "analyst"))
    denied(write(repo, "analyst", P + "workflow/04_analysis_plan.md", "rewritten\n"))
    allowed(write(repo, "analyst", P + "workflow/05_analysis.md"))  # other files unaffected
    # the human (main session) may still edit it
    allowed(call(repo, "Edit", {"file_path": str(plan), "old_string": "plan", "new_string": "new plan"}, None))


def test_unapproved_plan_is_editable_by_analyst(repo):
    plan = repo / "Projects" / "demo" / "workflow" / "04_analysis_plan.md"
    allowed(call(repo, "Edit", {"file_path": str(plan), "old_string": "plan", "new_string": "better plan"}, "analyst"))


def test_approval_phrase_in_bash_denied_everywhere(repo):
    for agent in (None, "analyst"):
        denied(bash(repo, agent, f"echo '{APPROVAL}' >> Projects/demo/workflow/04_analysis_plan.md"))
        denied(bash(repo, agent, "echo '- " + "Appro" + "ved:" + "hu" + "man' | tee x.txt"))


# ---------------------------------------------------------------------------
# G1: sensitive files
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", [".env", ".env.local", ".zshrc", ".envrc", ".ENV"])
def test_sensitive_files_denied_for_all_tools_and_sessions(repo, name):
    path = str(repo / name)
    for agent in (None, "analyst"):
        denied(call(repo, "Read", {"file_path": path}, agent))
        denied(call(repo, "Write", {"file_path": path, "content": "x"}, agent))
        denied(call(repo, "Edit", {"file_path": path, "old_string": "a", "new_string": "b"}, agent))
        denied(bash(repo, agent, f"cat {path}"))


def test_env_example_is_allowed_and_regular_commands_are_not_false_positives(repo):
    allowed(call(repo, "Read", {"file_path": str(repo / ".env.example")}, None))
    for agent in (None, "analyst"):
        allowed(bash(repo, agent, "cat .env.example"))
        allowed(bash(repo, agent, ".venv/bin/python -V"))
        allowed(bash(repo, agent, "python -c 'import os; print(os.environ.get(1))'"))


def test_main_session_general_write_allowed_but_env_read_denied(repo):
    allowed(write(repo, None, "README.md"))
    allowed(write(repo, None, "CLAUDE.md"))
    allowed(write(repo, None, P + "workflow/00_brief.md"))
    denied(call(repo, "Read", {"file_path": str(repo / ".env")}, None))


def test_symlink_to_env_read_denied(repo):
    link = repo / "innocent.txt"
    try:
        os.symlink(repo / ".env", link)
    except OSError:
        pytest.skip("symlinks not supported")
    denied(call(repo, "Read", {"file_path": str(link)}, None))


# ---------------------------------------------------------------------------
# MultiEdit / NotebookEdit
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("agent", ALL_AGENTS + ["general-purpose"])
def test_multiedit_and_notebookedit_denied_for_any_subagent_without_path_parsing(repo, agent):
    denied(call(repo, "MultiEdit", {"unexpected": "shape"}, agent))
    denied(call(repo, "NotebookEdit", {"anything": 1}, agent))
    denied(call(repo, "MultiEdit", {"file_path": str(repo / P / "pipeline/x.py"), "edits": []}, agent))


def test_multiedit_and_notebookedit_allowed_for_main_session(repo):
    allowed(call(repo, "MultiEdit", {"file_path": str(repo / "README.md"), "edits": [{"old_string": "a", "new_string": "b"}]}, None))
    allowed(call(repo, "NotebookEdit", {"notebook_path": str(repo / "Practice/n.ipynb"), "new_source": "x = 1"}, None))
    denied(call(repo, "MultiEdit", {"file_path": str(repo / "README.md"), "edits": [{"old_string": "a", "new_string": "- " + APPROVAL}]}, None))
    denied(call(repo, "MultiEdit", {"file_path": str(repo / ".env"), "edits": []}, None))


# ---------------------------------------------------------------------------
# G4 Bash
# ---------------------------------------------------------------------------
PROJ_CWD = "Projects/demo"


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x",
        "git -C . commit -m x",
        "git push origin main",
        "git add .",
        "git reset --hard",
        "git checkout main",
        "git restore x",
        "git rebase main",
        "git merge x",
        "git stash",
        "git clean -fd",
        "rm -rf outputs",
        "ls && rm x",
        "sudo ls",
        "chmod 777 x",
        "ssh host",
        "scp a b:c",
        "curl http://example.com",
        "wget http://example.com",
        "pip install x",
        "python -m pip install x",
        "uv pip install x",
        "npm install",
        "bash -c 'git commit -m x'",
        "FOO=1 git push",
    ],
)
def test_analyst_bash_denied(repo, command):
    denied(bash(repo, "analyst", command, cwd=repo / PROJ_CWD))


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "git diff --stat",
        "git log --oneline -3",
        "python main.py",
        "MPLBACKEND=Agg python main.py --output outputs/",
        "python main.py 2>&1",
        "python main.py > /dev/null 2>&1",
        "python main.py > outputs/log.txt 2>&1",
        "pytest -q",
        "pytest -q 2>&1 | tee outputs/pytest.log",
        "grep rm pipeline/load.py",
        "ls -la && cat pipeline/load.py | head",
        "python - <<'EOF'\nprint(1 > 0)\nrm = 1\nEOF",
        "sed -n '1,5p' pipeline/load.py",
        "sed -i 's/a/b/' pipeline/load.py",
        "cp outputs/a.csv outputs/b.csv",
        "mv outputs/a.csv outputs/c.csv",
        "echo done # a comment",
    ],
)
def test_analyst_bash_allowed(repo, command):
    allowed(bash(repo, "analyst", command, cwd=repo / PROJ_CWD))


@pytest.mark.parametrize(
    "command",
    [
        "python main.py > ../../README.md",
        "python main.py >> ../../CLAUDE.md",
        "echo x > ../../CLAUDE.md",
        "python main.py &> ../../x.log",
        "echo x | tee notes.txt",
        "echo x | tee ../../CLAUDE.md",
        "sed -i 's/a/b/' ../../CLAUDE.md",
        "sed -i -e 's/a/b/' tests/test_validation_z.py",
        "cp outputs/a.csv ../../CLAUDE.md",
        "cp -t ../../scripts outputs/a.csv",
        "mv outputs/a.csv ../../x.csv",
        "mv ../../CLAUDE.md outputs/",
        "python main.py > $OUT",
        "echo x > /tmp/outside.txt",
    ],
)
def test_analyst_bash_writes_outside_scope_denied(repo, command):
    denied(bash(repo, "analyst", command, cwd=repo / PROJ_CWD))


def test_validator_cannot_redirect_into_pipeline(repo):
    cwd = repo / PROJ_CWD
    denied(bash(repo, "validator", "echo x > pipeline/load.py", cwd=cwd))
    denied(bash(repo, "validator", "sed -i 's/a/b/' pipeline/load.py", cwd=cwd))
    allowed(bash(repo, "validator", "echo x > tests/test_validation_a.py", cwd=cwd))
    allowed(bash(repo, "validator", "pytest -q > workflow/logs/pytest.txt 2>&1", cwd=cwd))


def test_main_session_bash_is_not_restricted_by_g4(repo):
    allowed(bash(repo, None, "git commit -m 'message'"))
    allowed(bash(repo, None, "rm -f nothing.txt"))
    allowed(bash(repo, None, "echo hi > README.md"))


def test_unparsable_subagent_bash_fails_closed(repo):
    denied(bash(repo, "analyst", "echo 'unterminated", cwd=repo / PROJ_CWD))


# ---------------------------------------------------------------------------
# G5 fail closed + unhandled tools
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("stdin", ["{not json", "", "[]", "null", '"text"', "{}", '{"tool_name": "Write"}', '{"tool_name": "Write", "tool_input": []}'])
def test_broken_input_exits_2_with_disable_hint(repo, stdin):
    code, err = run_raw(repo, stdin)
    assert code == 2
    assert "settings.json" in err


def test_write_without_file_path_fails_closed(repo):
    code, _ = call(repo, "Write", {"content": "x"}, None)
    assert code == 2


def test_unhandled_tools_are_ignored(repo):
    allowed(call(repo, "Glob", {"pattern": "**/.env"}, "analyst"))
    allowed(call(repo, "Grep", {"pattern": "x", "path": ".env"}, "analyst"))


# ---------------------------------------------------------------------------
# settings.json registration
# ---------------------------------------------------------------------------
def test_settings_registers_guard():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    entries = settings["hooks"]["PreToolUse"]
    guard_entries = [e for e in entries if any("guard.py" in h.get("command", "") for h in e["hooks"])]
    assert len(guard_entries) == 1
    entry = guard_entries[0]
    assert set(entry["matcher"].split("|")) == {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "Read"}
    hook = entry["hooks"][0]
    assert hook["type"] == "command"
    assert hook["command"].startswith("python3 ")
    assert "$CLAUDE_PROJECT_DIR" in hook["command"]
    assert hook["command"].rstrip().endswith("|| exit 2")


def test_registered_command_blocks_when_guard_crashes_or_is_missing(tmp_path):
    # the "|| exit 2" wrapper turns any non-2 failure (missing file, crash, no python) into a block
    proc = subprocess.run(
        ["sh", "-c", f'{sys.executable} "{tmp_path}/missing_guard.py" || exit 2'],
        input="{}", capture_output=True, text=True,
    )
    assert proc.returncode == 2
    crash = tmp_path / "crash.py"
    crash.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    proc = subprocess.run(["sh", "-c", f'{sys.executable} "{crash}" || exit 2'], capture_output=True, text=True)
    assert proc.returncode == 2
