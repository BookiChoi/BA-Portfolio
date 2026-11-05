# Human-led analysis pipeline

## Purpose

I (the human) choose the company, write the business questions, the insights and the recommendations.
AI agents research, give feedback on my questions, plan and run the analysis, validate the numbers,
argue against my conclusions and forecast the impact. Each stage leaves a numbered file in
`Projects/<slug>/workflow/`, and the first line of every file names its author
(`Author: human` or `Author: ai/<agent>`). Agents hand work over through these files only.

Rules that apply to every number: it must come from executed code (or a cited source), and news
sources are summarized with a link, never copied.

## Stages

| Stage | File in `workflow/` | Owner | Notes |
|---|---|---|---|
| 00 Brief | `00_brief.md` | human | company, why, what I found myself |
| 01 Research | `01_research.md` | AI `researcher` (mode `research`) | context, news, candidate datasets |
| 02 Questions | `02_questions.md` | human | decision, question, hypothesis, metric, data needed, decision rule |
| 02 Feedback | `02_questions_feedback.md` | AI `question-coach` | critique only; it does not rewrite the questions |
| 03 Data plan | `03_data_plan.md` | AI `researcher` (mode `data-feasibility`) | GO / NO-GO per question |
| 04 Analysis plan | `04_analysis_plan.md` | AI `analyst` (phase A) | metrics, methods, assumptions, tests; stops after the plan |
| 05 Analysis | `05_analysis.md` | AI `analyst` (phase B) | runs only the approved plan |
| 06 Validation | `06_validation.md` | AI `validator` | independent recomputation, PASS/FAIL per number |
| 06 Fail resolution | `06_fail_resolution.md` | human | only needed after a FAIL |
| 07 Insights | `07_insights.md` | human | claim, evidence with file locations, interpretation |
| 08 Critique | `08_critique.md` | AI `critic` | alternative explanations, confounders, limits; no code execution |
| 09 Recommendations | `09_recommendations.md` | human | owner, rationale, assumptions (low/base/high), KPI, risks |
| 10 Impact | `10_impact.md`, `10_impact_assumptions.json` | AI `impact-modeler` | scenarios and sensitivity, experiment design |

Human documents have `Status:` on line 2 (`draft`, `final`; document 02 also has `ready-for-coach`).
`scripts/project_state.py <slug>` reads the files and prints which stage is next and who is up.

## Human gates

The pipeline stops at these points until I act:

1. **03 data approval.** I read the GO / NO-GO verdict, make sure the data is in `data/` (or confirm
   the URL), and add the approval line to `03_data_plan.md` myself.
2. **04 analysis plan approval.** I review the plan and add the approval line to `04_analysis_plan.md`.
   The analyst does not run phase B without it.
3. **06 FAIL resolution.** If the validation report contains a FAIL, nothing continues automatically.
   I either write `06_fail_resolution.md` (`Decision: accept-with-caveat` or `drop-question`) or move
   05 and 06 into `workflow/archive/runN/` to run the analysis again.
4. **07 key numbers.** Before writing insights I reproduce one or two key numbers myself.
   This one is a working agreement: the tools mark `07_insights.md` as final when I set its status,
   and cannot check whether I actually reproduced anything.

## How it is run

- `python scripts/new_project.py <slug> --company "<name>"` copies `Projects/_template/`.
- `/run-project <slug>` (a skill that only I can start) runs at most one AI stage per call, then
  stops. On my turn it only explains what to do. It never edits human documents, never writes the
  approval line and never pushes.

## Safety measures

- **Write guard hook** (`.claude/hooks/guard.py`, registered in `.claude/settings.json` for Write, Edit,
  MultiEdit, NotebookEdit, Bash and Read). For subagents it allows writes only inside the active
  project (`.claude/active_project`, set by the skill), only to the files on that agent's allow list,
  never to the human documents, `.claude/`, `CLAUDE.md`, `scripts/`, `Learning/`, `Practice/` or the
  template. A document that already carries the approval line cannot be modified by a subagent.
  It fails closed: unreadable input or an internal error blocks the call.
- **The approval line is written by the human only.** The hook refuses to let any Claude session
  (main session included) write a line that starts with it. It cannot stop me from typing it in an
  editor, which is the intended way.
- **Secrets.** `.env*` (except `.env.example`), `.zshrc` and `.envrc` cannot be read or written
  through the guarded tools.
- **Least privilege.** Each agent has only the tools it needs: `researcher` has web access but no Bash,
  `question-coach` and `critic` have no Bash, only `analyst`, `validator` and `impact-modeler` can run
  code. Agents do not commit; the `/run-project` skill commits their files.
- **Commit labels and checks.** Commits made with AI help start with `[AI-<TYPE>]`
  (`PROJECT`, `FEAT`, `CHORE`, `FIX`) and keep the Co-Authored-By trailer; project work uses
  `[AI-PROJECT] <slug> <stage>: <summary>` with fixed stage names such as `04-analysis-plan`.
  `python scripts/check_commits.py` checks the unpushed commits for these labels, for data files under
  `Projects/*/data/` and for files over 5 MB, and warns about `Claude-Session:` trailers. Run it
  before pushing.

## Known limits

- The Bash check is best effort. It reads the command text only, so a program that writes files
  internally (for example a Python script) is not seen. `Grep` and `Glob` are not covered by the hook.
- The hook has unit tests and a few manual probes in a live session (blocked `.envrc` read, blocked
  subagent write to `.claude/`, blocked approval line). The `/run-project` skill and the agents have not
  been run end to end on a real project yet, and the quality of their output has not been evaluated.
- The existing Airbnb and Online Retail projects predate this pipeline and have no `workflow/` folder.
