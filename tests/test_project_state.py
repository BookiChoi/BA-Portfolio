"""Tests for scripts/project_state.py (fake projects in tmp_path only).

The approval phrase is built from pieces so this file never contains it literally.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "project_state.py"
GUARD = REPO / ".claude" / "hooks" / "guard.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ps = _load("project_state_under_test", SCRIPT)

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
NOT_APPROVALS = [
    "note: " + APPROVAL + " is added later",
    "Appro" + "ved: hu" + "mans",
    "Appro" + "ved by a hu" + "man",
    "",
]


# ---------------------------------------------------------------------------
# document builders
# ---------------------------------------------------------------------------
def human(status: str, body: str = "text") -> str:
    return f"Author: human\nStatus: {status}\n{body}\n"


def ai(agent: str, body: str = "text") -> str:
    return f"Author: ai/{agent}\n{body}\n"


def approved(text: str, variant: str = APPROVAL) -> str:
    return text + variant + "\n"


F00 = human("final")
F01 = ai("researcher")
F02_DRAFT = human("draft")
F02_READY = human("ready-for-coach")
F02_FINAL = human("final")
FB = ai("question-coach")
F03 = ai("researcher")
F04 = ai("analyst")
F05 = ai("analyst")
F06_PASS = ai("validator", "| number | analyst | PASS/FAIL |\n|---|---|---|\n| a | 1 | PASS |")
F06_FAIL = ai("validator", "| number | analyst | PASS/FAIL |\n|---|---|---|\n| a | 1 | PASS |\n| b | 2 | **FAIL** |")
F07 = human("final")
F08 = ai("critic")
F09 = human("final")
F10 = ai("impact-modeler")


def resolution(decision: str = "accept-with-caveat", author: str = "human", status: str = "final") -> str:
    return f"Author: {author}\nStatus: {status}\nDecision: {decision}\nWhy: caveat noted\n"


def make(tmp_path: Path, files: dict[str, str]) -> Path:
    projects = tmp_path / "Projects"
    wf = projects / "demo" / "workflow"
    wf.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = wf / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return projects


def state(tmp_path: Path, files: dict[str, str]) -> dict:
    return ps.decide("demo", make(tmp_path, files))


BASE_03 = {"00_brief.md": F00, "01_research.md": F01, "02_questions.md": F02_FINAL}
BASE_04 = {**BASE_03, "03_data_plan.md": approved(F03)}
BASE_05 = {**BASE_04, "04_analysis_plan.md": approved(F04)}
BASE_06 = {**BASE_05, "05_analysis.md": F05}
BASE_07 = {**BASE_06, "06_validation.md": F06_PASS}
BASE_08 = {**BASE_07, "07_insights.md": F07}
BASE_09 = {**BASE_08, "08_critique.md": F08}
BASE_10 = {**BASE_09, "09_recommendations.md": F09}


def check(result: dict, stage: str, actor: str, agent: str | None = None, mode: str | None = None):
    assert result["stage"] == stage, result
    assert result["next_actor"] == actor
    assert result["agent"] == agent
    assert result["mode"] == mode


# ---------------------------------------------------------------------------
# every branch, in order
# ---------------------------------------------------------------------------
def test_empty_workflow_starts_with_human_brief(tmp_path):
    check(state(tmp_path, {}), "00_brief", "human")


def test_brief_not_final_is_human(tmp_path):
    check(state(tmp_path, {"00_brief.md": human("draft")}), "00_brief", "human")


def test_research_missing_goes_to_researcher_mode_research(tmp_path):
    r = state(tmp_path, {"00_brief.md": F00})
    check(r, "01_research", "ai", "researcher", "research")
    assert r["inputs"] == ["workflow/00_brief.md"]
    assert r["expected_outputs"] == ["workflow/01_research.md"]


def test_empty_research_file_counts_as_missing(tmp_path):
    check(state(tmp_path, {"00_brief.md": F00, "01_research.md": "  \n"}), "01_research", "ai", "researcher", "research")


def test_questions_missing_or_draft_is_human(tmp_path):
    check(state(tmp_path, {"00_brief.md": F00, "01_research.md": F01}), "02_questions_draft", "human")
    check(state(tmp_path, {"00_brief.md": F00, "01_research.md": F01, "02_questions.md": F02_DRAFT}),
          "02_questions_draft", "human")


def test_ready_for_coach_without_feedback_goes_to_coach(tmp_path):
    r = state(tmp_path, {"00_brief.md": F00, "01_research.md": F01, "02_questions.md": F02_READY})
    check(r, "02_coach_feedback", "ai", "question-coach")
    assert r["expected_outputs"] == ["workflow/02_questions_feedback.md"]


def test_feedback_present_but_questions_not_final_is_human(tmp_path):
    files = {"00_brief.md": F00, "01_research.md": F01, "02_questions.md": F02_READY, "02_questions_feedback.md": FB}
    check(state(tmp_path, files), "02_apply_feedback", "human")


def test_questions_final_without_coach_skips_feedback(tmp_path):
    check(state(tmp_path, BASE_03), "03_data_plan", "ai", "researcher", "data-feasibility")


def test_data_plan_without_approval_is_human(tmp_path):
    check(state(tmp_path, {**BASE_03, "03_data_plan.md": F03}), "03_review", "human")


def test_analysis_plan_phase_a(tmp_path):
    check(state(tmp_path, BASE_04), "04_plan", "ai", "analyst", "phase-a")


def test_analysis_plan_without_approval_is_human(tmp_path):
    check(state(tmp_path, {**BASE_04, "04_analysis_plan.md": F04}), "04_review", "human")


def test_analysis_phase_b_after_approval(tmp_path):
    check(state(tmp_path, BASE_05), "05_analysis", "ai", "analyst", "phase-b")


def test_validation_missing_goes_to_validator(tmp_path):
    check(state(tmp_path, BASE_06), "06_validation", "ai", "validator")


def test_validation_fail_stops_for_human(tmp_path):
    r = state(tmp_path, {**BASE_06, "06_validation.md": F06_FAIL})
    check(r, "06_fail_decision", "human")
    assert r["blockers"]


def test_validation_pass_goes_to_insights(tmp_path):
    check(state(tmp_path, BASE_07), "07_insights", "human")


def test_insights_final_goes_to_critic(tmp_path):
    check(state(tmp_path, BASE_08), "08_critique", "ai", "critic")


def test_critique_done_goes_to_recommendations(tmp_path):
    check(state(tmp_path, BASE_09), "09_recommendations", "human")


def test_recommendations_final_goes_to_impact_modeler(tmp_path):
    r = state(tmp_path, BASE_10)
    check(r, "10_impact", "ai", "impact-modeler")
    assert "workflow/10_impact_assumptions.json" in r["expected_outputs"]


def test_everything_done(tmp_path):
    check(state(tmp_path, {**BASE_10, "10_impact.md": F10}), "done", "done")


# ---------------------------------------------------------------------------
# Status line handling
# ---------------------------------------------------------------------------
def test_status_line_must_be_second_line_and_valid(tmp_path):
    third_line = "Author: human\n\nStatus: final\n"
    r = state(tmp_path, {"00_brief.md": third_line})
    check(r, "00_brief", "human")
    assert r["blockers"]
    r = state(tmp_path, {"00_brief.md": "Author: human\nStatus: finished\n"})
    assert "unknown Status" in r["blockers"][0]
    r = state(tmp_path, {"00_brief.md": "Author: human\n# no status\n"})
    assert r["blockers"]


def test_status_is_case_insensitive(tmp_path):
    check(state(tmp_path, {"00_brief.md": "Author: human\nSTATUS: FINAL\n"}), "01_research", "ai", "researcher", "research")


def test_ready_for_coach_is_not_valid_for_brief(tmp_path):
    r = state(tmp_path, {"00_brief.md": human("ready-for-coach")})
    check(r, "00_brief", "human")
    assert r["blockers"]


# ---------------------------------------------------------------------------
# approval line variants (same rule as the hook)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("variant", APPROVAL_VARIANTS)
def test_approval_variants_count_for_03_and_04(tmp_path, variant):
    files = {**BASE_03, "03_data_plan.md": approved(F03, variant)}
    check(state(tmp_path, files), "04_plan", "ai", "analyst", "phase-a")
    files = {**BASE_04, "04_analysis_plan.md": approved(F04, variant)}
    check(state(tmp_path / "b", files), "05_analysis", "ai", "analyst", "phase-b")


@pytest.mark.parametrize("text", NOT_APPROVALS)
def test_non_approval_lines_do_not_count(tmp_path, text):
    files = {**BASE_03, "03_data_plan.md": F03 + text + "\n"}
    check(state(tmp_path, files), "03_review", "human")


def test_approval_regex_matches_the_hook():
    guard = _load("guard_under_test", GUARD)
    for text in APPROVAL_VARIANTS + NOT_APPROVALS:
        sample = "Author: x\n" + text + "\n"
        assert ps.has_approval_line(sample) == guard.has_approval_line(sample), text


# ---------------------------------------------------------------------------
# FAIL detection
# ---------------------------------------------------------------------------
def test_pass_fail_header_and_prose_are_not_a_fail(tmp_path):
    body = "Notes: a FAIL would block the run.\n| number | PASS/FAIL |\n|---|---|\n| a | PASS |"
    check(state(tmp_path, {**BASE_06, "06_validation.md": ai("validator", body)}), "07_insights", "human")


@pytest.mark.parametrize("cell", ["FAIL", "**FAIL**", " fail ", "`FAIL`"])
def test_fail_cell_variants(tmp_path, cell):
    body = f"| number | PASS/FAIL |\n|---|---|\n| a | {cell} |"
    check(state(tmp_path, {**BASE_06, "06_validation.md": ai("validator", body)}), "06_fail_decision", "human")


def test_overall_line_with_fail(tmp_path):
    check(state(tmp_path, {**BASE_06, "06_validation.md": ai("validator", "Overall: FAIL")}), "06_fail_decision", "human")


# ---------------------------------------------------------------------------
# 06 fail resolution file
# ---------------------------------------------------------------------------
FAILED = {**BASE_06, "06_validation.md": F06_FAIL}


@pytest.mark.parametrize("decision", ["accept-with-caveat", "drop-question"])
def test_valid_resolution_unblocks(tmp_path, decision):
    r = state(tmp_path, {**FAILED, "06_fail_resolution.md": resolution(decision)})
    check(r, "07_insights", "human")
    assert r["info"]["fail_resolution"] == decision


@pytest.mark.parametrize(
    "content",
    [
        resolution("ignore-it"),
        resolution(status="draft"),
        resolution(author="ai/analyst"),
        "Author: human\nStatus: final\n",
        "Author: human\nStatus: final\n\nDecision: accept-with-caveat\n",  # Decision must be line 3
    ],
)
def test_invalid_resolution_keeps_blocking(tmp_path, content):
    r = state(tmp_path, {**FAILED, "06_fail_resolution.md": content})
    check(r, "06_fail_decision", "human")
    assert r["blockers"]


def test_resolution_is_ignored_when_validation_has_no_fail(tmp_path):
    check(state(tmp_path, {**BASE_06, "06_validation.md": F06_PASS, "06_fail_resolution.md": resolution()}),
          "07_insights", "human")


# ---------------------------------------------------------------------------
# workflow/archive/ is ignored
# ---------------------------------------------------------------------------
def test_archiving_05_and_06_restarts_analysis_phase_b(tmp_path):
    files = {
        **BASE_05,
        "archive/run1/05_analysis.md": F05,
        "archive/run1/06_validation.md": F06_FAIL,
        "archive/run1/06_fail_resolution.md": resolution(),
    }
    check(state(tmp_path, files), "05_analysis", "ai", "analyst", "phase-b")


def test_archive_does_not_hide_or_satisfy_files_in_workflow(tmp_path):
    files = {**BASE_06, "06_validation.md": F06_PASS, "archive/run1/06_validation.md": F06_FAIL}
    check(state(tmp_path, files), "07_insights", "human")  # the FAIL inside archive/ is ignored


def test_archiving_03_after_no_go_reruns_feasibility(tmp_path):
    files = {**BASE_03, "archive/run1/03_data_plan.md": approved(F03), "archive/run1/04_analysis_plan.md": approved(F04)}
    check(state(tmp_path, files), "03_data_plan", "ai", "researcher", "data-feasibility")


def test_archived_feedback_allows_new_coach_round(tmp_path):
    files = {"00_brief.md": F00, "01_research.md": F01, "02_questions.md": F02_READY,
             "archive/run1/02_questions_feedback.md": FB}
    check(state(tmp_path, files), "02_coach_feedback", "ai", "question-coach")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def run_cli(*args: str):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_cli_prints_json_with_expected_keys(tmp_path):
    projects = make(tmp_path, BASE_05)
    proc = run_cli("demo", "--projects-dir", str(projects))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert {"slug", "stage", "next_actor", "agent", "action", "blockers", "inputs", "expected_outputs"} <= set(data)
    assert data["slug"] == "demo" and data["stage"] == "05_analysis"


@pytest.mark.parametrize("slug", ["Demo", "-demo", "de_mo", "../demo", "a--b"])
def test_cli_rejects_invalid_slug(tmp_path, slug):
    # "--" keeps argparse from reading a leading-hyphen slug as an option
    proc = run_cli("--projects-dir", str(make(tmp_path, {})), "--", slug)
    assert proc.returncode == 1
    assert "error" in json.loads(proc.stdout)


def test_cli_missing_project_is_an_error(tmp_path):
    proc = run_cli("nothing-here", "--projects-dir", str(make(tmp_path, {})))
    assert proc.returncode == 1
    assert "error" in json.loads(proc.stdout)
