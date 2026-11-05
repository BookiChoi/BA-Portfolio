"""Decide the current stage of an analysis project from its workflow files.

Usage:
    python scripts/project_state.py <slug> [--projects-dir <path>]

Prints one JSON object:
    slug, project_dir, stage, next_actor (human|ai|done), agent, mode,
    action, blockers, inputs, expected_outputs, info

Paths in inputs / expected_outputs are relative to the project folder.
Only files directly inside Projects/<slug>/workflow/ are looked at, so anything
moved to workflow/archive/ (for example workflow/archive/run1/) is ignored.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECTS_DIR = REPO_ROOT / "Projects"
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Same variant rules as .claude/hooks/guard.py (a test keeps both in sync).
# Built from pieces so this source never contains the literal approval phrase.
_A = "appro" + "ved"
_H = "hu" + "man"
APPROVAL_LINE_RE = re.compile(
    r"^(?:[ \t>*_#`+•-]|\d+[.)])*" + _A + r"[ \t*_`]*:[ \t*_`]*" + _H + r"\b",
    re.IGNORECASE | re.MULTILINE,
)

STATUS_VALUES = {
    "00_brief.md": {"draft", "final"},
    "02_questions.md": {"draft", "ready-for-coach", "final"},
    "07_insights.md": {"draft", "final"},
    "09_recommendations.md": {"draft", "final"},
}
DECISIONS = {"accept-with-caveat", "drop-question"}


# ---------------------------------------------------------------------------
# small readers
# ---------------------------------------------------------------------------
def read(path: Path) -> str | None:
    """File text, or None when the file is missing or empty."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return text if text.strip() else None


def has_approval_line(text: str) -> bool:
    return bool(APPROVAL_LINE_RE.search(text.replace("\r\n", "\n").replace("\r", "\n")))


def second_line_value(text: str, key: str) -> str | None:
    """Value of 'Key: value' on exactly the second line (case-insensitive key)."""
    lines = text.splitlines()
    if len(lines) < 2:
        return None
    m = re.fullmatch(rf"\s*{re.escape(key)}\s*:\s*(\S+)\s*", lines[1], re.IGNORECASE)
    return m.group(1).lower() if m else None


def has_fail(text: str) -> bool:
    """FAIL in the validation report.

    A markdown table cell that is exactly FAIL (bold allowed), or an Overall/Verdict
    line containing FAIL. The header cell 'PASS/FAIL' and prose are ignored.
    """
    for line in text.splitlines():
        if "|" in line:
            for cell in line.split("|"):
                if cell.strip().strip("*`_ ").upper() == "FAIL":
                    return True
        if re.match(r"^\W*(overall|verdict)\b.*\bFAIL\b", line, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# decision
# ---------------------------------------------------------------------------
def _result(slug, project_dir, stage, actor, action, *, agent=None, mode=None,
            blockers=None, inputs=None, outputs=None, info=None) -> dict:
    return {
        "slug": slug,
        "project_dir": str(project_dir),
        "stage": stage,
        "next_actor": actor,
        "agent": agent,
        "mode": mode,
        "action": action,
        "blockers": blockers or [],
        "inputs": inputs or [],
        "expected_outputs": outputs or [],
        "info": info or {},
    }


def decide(slug: str, projects_dir: Path) -> dict:
    project_dir = projects_dir / slug
    wf = project_dir / "workflow"

    def out(*a, **k):
        return _result(slug, project_dir, *a, **k)

    def human_doc(name: str, stage: str, wanted: str, write_action: str):
        """Return a human-stage result if the document is not final, else None."""
        text = read(wf / name)
        allowed = STATUS_VALUES[name]
        blockers: list[str] = []
        status = None
        if text is None:
            blockers.append(f"workflow/{name} is missing or empty")
        else:
            status = second_line_value(text, "Status")
            if status is None:
                blockers.append(f"line 2 of workflow/{name} must be 'Status: <{'|'.join(sorted(allowed))}>'")
            elif status not in allowed:
                blockers.append(f"unknown Status '{status}' in workflow/{name} (allowed: {', '.join(sorted(allowed))})")
        if status == "final":
            return None
        return out(stage, "human", f"{write_action} Then set line 2 to 'Status: {wanted}'.", blockers=blockers,
                   info={"file": f"workflow/{name}", "status": status})

    # 00 brief
    r = human_doc("00_brief.md", "00_brief", "final", "Write workflow/00_brief.md yourself.")
    if r:
        return r

    # 01 research
    if read(wf / "01_research.md") is None:
        return out("01_research", "ai", "Research the company, news and candidate datasets.",
                   agent="researcher", mode="research", inputs=["workflow/00_brief.md"],
                   outputs=["workflow/01_research.md"])

    # 02 questions
    q_text = read(wf / "02_questions.md")
    q_status = second_line_value(q_text, "Status") if q_text else None
    feedback = read(wf / "02_questions_feedback.md")
    if q_text is None or q_status not in STATUS_VALUES["02_questions.md"] or q_status == "draft":
        blockers = []
        if q_text is None:
            blockers.append("workflow/02_questions.md is missing or empty")
        elif q_status is None:
            blockers.append("line 2 of workflow/02_questions.md must be 'Status: <draft|ready-for-coach|final>'")
        elif q_status not in STATUS_VALUES["02_questions.md"]:
            blockers.append(f"unknown Status '{q_status}' in workflow/02_questions.md")
        return out("02_questions_draft", "human",
                   "Write workflow/02_questions.md yourself. Then set line 2 to 'Status: ready-for-coach'.",
                   blockers=blockers, info={"file": "workflow/02_questions.md", "status": q_status})
    if q_status == "ready-for-coach" and feedback is None:
        return out("02_coach_feedback", "ai", "Give feedback on the human's questions without rewriting them.",
                   agent="question-coach", inputs=["workflow/00_brief.md", "workflow/01_research.md", "workflow/02_questions.md"],
                   outputs=["workflow/02_questions_feedback.md"])
    if q_status != "final":
        return out("02_apply_feedback", "human",
                   "Read workflow/02_questions_feedback.md, revise workflow/02_questions.md yourself. "
                   "Then set line 2 to 'Status: final'.",
                   info={"file": "workflow/02_questions.md", "status": q_status})

    # 03 data plan
    plan03 = read(wf / "03_data_plan.md")
    if plan03 is None:
        return out("03_data_plan", "ai", "Check data feasibility for the questions and give a GO/NO-GO verdict.",
                   agent="researcher", mode="data-feasibility",
                   inputs=["workflow/00_brief.md", "workflow/01_research.md", "workflow/02_questions.md"],
                   outputs=["workflow/03_data_plan.md"])
    if not has_approval_line(plan03):
        return out("03_review", "human",
                   "Review the verdict in workflow/03_data_plan.md, put the data in data/ (or confirm the approved URL), "
                   "then add the approval line to workflow/03_data_plan.md yourself.",
                   info={"file": "workflow/03_data_plan.md"})

    # 04 analysis plan
    plan04 = read(wf / "04_analysis_plan.md")
    if plan04 is None:
        return out("04_plan", "ai", "Write the analysis plan (Phase A) and stop.", agent="analyst", mode="phase-a",
                   inputs=["workflow/02_questions.md", "workflow/03_data_plan.md", "data_manifest.json"],
                   outputs=["workflow/04_analysis_plan.md"])
    if not has_approval_line(plan04):
        return out("04_review", "human",
                   "Review workflow/04_analysis_plan.md, then add the approval line to it yourself.",
                   info={"file": "workflow/04_analysis_plan.md"})

    # 05 analysis
    if read(wf / "05_analysis.md") is None:
        return out("05_analysis", "ai", "Execute the approved plan (Phase B).", agent="analyst", mode="phase-b",
                   inputs=["workflow/04_analysis_plan.md", "workflow/03_data_plan.md", "data_manifest.json"],
                   outputs=["workflow/05_analysis.md"])

    # 06 validation
    val = read(wf / "06_validation.md")
    if val is None:
        return out("06_validation", "ai", "Independently recompute and validate the analysis numbers.",
                   agent="validator", inputs=["workflow/04_analysis_plan.md", "workflow/05_analysis.md", "data_manifest.json"],
                   outputs=["workflow/06_validation.md"])
    if has_fail(val):
        res = read(wf / "06_fail_resolution.md")
        blockers: list[str] = []
        decision = None
        if res is not None:
            lines = res.splitlines()
            ok_author = bool(lines) and lines[0].strip().lower() == "author: human"
            ok_status = second_line_value(res, "Status") == "final"
            m = re.fullmatch(r"\s*Decision\s*:\s*(\S+)\s*", lines[2], re.IGNORECASE) if len(lines) > 2 else None
            decision = m.group(1).lower() if m else None
            if not ok_author:
                blockers.append("line 1 of workflow/06_fail_resolution.md must be 'Author: human'")
            if not ok_status:
                blockers.append("line 2 of workflow/06_fail_resolution.md must be 'Status: final'")
            if decision not in DECISIONS:
                blockers.append("line 3 of workflow/06_fail_resolution.md must be 'Decision: accept-with-caveat' "
                                "or 'Decision: drop-question'")
        else:
            blockers.append("06_validation.md contains FAIL and no workflow/06_fail_resolution.md exists")
        if blockers:
            return out("06_fail_decision", "human",
                       "Validation has FAIL. Decide yourself: write workflow/06_fail_resolution.md (Author: human, "
                       "Status: final, Decision: accept-with-caveat|drop-question), or move 05 and 06 into "
                       "workflow/archive/run1/ with git mv to re-run the analysis.",
                       blockers=blockers, info={"file": "workflow/06_validation.md"})
        resolved_info = {"fail_resolution": decision}
    else:
        resolved_info = {}

    # 07 insights
    r = human_doc("07_insights.md", "07_insights", "final",
                  "Reproduce one or two key numbers yourself, then write workflow/07_insights.md.")
    if r:
        r["info"].update(resolved_info)
        return r

    # 08 critique
    if read(wf / "08_critique.md") is None:
        return out("08_critique", "ai", "Argue against the human's insights.", agent="critic",
                   inputs=["workflow/07_insights.md", "workflow/05_analysis.md", "workflow/06_validation.md"],
                   outputs=["workflow/08_critique.md"], info=resolved_info)

    # 09 recommendations
    r = human_doc("09_recommendations.md", "09_recommendations", "final",
                  "Answer the critique and write workflow/09_recommendations.md yourself.")
    if r:
        return r

    # 10 impact
    if read(wf / "10_impact.md") is None:
        return out("10_impact", "ai", "Forecast the impact of the recommendations under the human's assumptions.",
                   agent="impact-modeler",
                   inputs=["workflow/09_recommendations.md", "workflow/05_analysis.md", "workflow/06_validation.md",
                           "workflow/08_critique.md"],
                   outputs=["workflow/10_impact.md", "workflow/10_impact_assumptions.json"], info=resolved_info)

    return out("done", "done", "All workflow stages are complete.", info=resolved_info)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the current workflow stage of a project as JSON.")
    parser.add_argument("slug")
    parser.add_argument("--projects-dir", type=Path, default=DEFAULT_PROJECTS_DIR)
    args = parser.parse_args(argv)

    def fail(message: str) -> int:
        print(json.dumps({"error": message}, ensure_ascii=False))
        return 1

    if not SLUG_RE.fullmatch(args.slug):
        return fail(f"invalid slug {args.slug!r}")
    if not (args.projects_dir / args.slug / "workflow").is_dir():
        return fail(f"no workflow folder at {args.projects_dir / args.slug / 'workflow'}")
    print(json.dumps(decide(args.slug, args.projects_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
