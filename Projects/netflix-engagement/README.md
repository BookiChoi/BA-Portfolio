# Netflix: Do genre shares of viewing hours alternate by half-year?

## Summary

- **Company:** Netflix
- **Business question (one line):** Among genres with an average share of at least 5%, does any genre's share of viewing hours move the same way in every H1-to-H2 transition and the opposite way in every H2-to-H1 transition, by at least 2 percentage points (pp) each time, from H1 2023 to H1 2026? (`workflow/02_questions.md`, Q1)
- **Key finding (one line):** "Under the rule I set before the analysis [...], none of the tested genre groups passes in Netflix's seven half-year reports (H1 2023 to H1 2026). This is an absence of evidence under a strict rule and a coarse labelling, not proof that no seasonality exists." (`workflow/07_insights.md`, I1)

## 1. What this is

- **Scope:** one business question (Q1). The decision it serves is how content planning and release scheduling leads weight genres in the second-half (Jul-Dec) release and licensing plan compared with the first half (`workflow/02_questions.md`).
- **Question:** see the Summary above. The pass rule had to hold in three checks: all labelled titles; excluding the 10 titles with the most hours in each half-year; and new versus carried-over titles separately.
- **Result:** no genre passes at 2 pp, and none passes at the 1.5 pp and 3 pp sensitivity thresholds. Check 1 alone already fails: the best margin is 0.49 pp (Sci-Fi & Fantasy). The result is an absence of evidence under a strict rule and a coarse labelling. I did not test whether the rule would detect a seasonal pattern if one were planted (`workflow/07_insights.md`).
- **Raw data:** not in this repo. The repo holds code, small aggregated tables and charts (`outputs/`), and the workflow documents.

## 2. Who did what

Commit prefixes are copied from `git log`. Owner and file are taken from the `Author:` line of each document.

| Stage | Owner | File | Commit prefix |
|---|---|---|---|
| 00 Brief | human | `workflow/00_brief.md` | `[PROJECT] netflix-engagement 00-brief` (scaffold: `00-init`) |
| 01 Research | AI (researcher) | `workflow/01_research.md` | `[AI-PROJECT] netflix-engagement 01-research` |
| 01 Source check of the research | human | `workflow/01_research_review.md` | `[PROJECT] netflix-engagement 01-review` |
| 01 Data profile of the source reports | AI (main session) | `workflow/01b_data_profile.md`, `outputs/profile/`, `pipeline/profile_reports.py` | `[AI-PROJECT] netflix-engagement 01-data-profile` |
| 01 Source URLs in the manifest | human | `data_manifest.json` | `[PROJECT] netflix-engagement 01-manifest` |
| 02 Business questions | human | `workflow/02_questions.md` | `[PROJECT] netflix-engagement 02-questions` |
| 02 Question feedback | AI (question-coach) | `workflow/02_questions_feedback.md` | `[AI-PROJECT] netflix-engagement 02-feedback` |
| 03 Data feasibility (GO/NO-GO) | AI (researcher) | `workflow/03_data_plan.md` | `[AI-PROJECT] netflix-engagement 03-data-plan` |
| 03 Approval, decisions and IMDb amendment | human | `workflow/03_data_plan.md` | `[PROJECT] netflix-engagement 03-data-plan` (approval), `03-amend` (IMDb) |
| 04 Analysis plan (two drafts) | AI (analyst) | `workflow/04_analysis_plan.md` | `[AI-PROJECT] netflix-engagement 04-analysis-plan` |
| 04 Genre mapping table | human | `config/genre_mapping.csv`, `config/genre_mapping_notes.md` | `[PROJECT] netflix-engagement 04-mapping` |
| 04 Plan approval and amendment | human | `workflow/04_analysis_plan.md` | `[PROJECT] netflix-engagement 04-plan` |
| 05 Analysis execution (stopped twice, see section 4) | AI (analyst) | `workflow/05_analysis.md`, `workflow/05a_scope_stop.md`, `workflow/05b_pilot_stop.md`, `pipeline/`, `outputs/q1/` | `[AI-PROJECT] netflix-engagement 05-analysis` |
| 05 Pilot check | human (with an AI first pass) | `workflow/05_pilot_check` | `[PROJECT] netflix-engagement 05-pilot` |
| 06 Validation (PASS/FAIL) | AI (validator) | `workflow/06_validation.md`, `tests/test_validation_*.py` | `[AI-PROJECT] netflix-engagement 06-validation` |
| 07 Insights | human | `workflow/07_insights.md` | `[PROJECT] netflix-engagement 07-insights` |
| 08 Critique | AI (critic) | `workflow/08_critique.md` | `[AI-PROJECT] netflix-engagement 08-critique` |
| 09 Recommendations | human | `workflow/09_recommendations.md` | `[PROJECT] netflix-engagement 09-recommendations` |
| 10 Impact forecast | skipped | none | none |

Step 10 is skipped because there is no validated seasonal effect to model (`workflow/09_recommendations.md`).

## 3. Human gates and decisions

- **Gate 1, data plan (03):** the researcher's verdict was GO (conditional). The human approved it with decisions on the genre source, the primary-genre rule, a pilot, a coverage rule and multiple testing (`workflow/03_data_plan.md`, "Human decisions at Gate 1").
- **Amendment to Gate 1 (03):** the genre source was changed from TMDB to the IMDb Non-Commercial Datasets (`workflow/03_data_plan.md`, "Amendment to Gate 1"; commit `03-amend`). The genre mapping table was committed before any genre share was computed.
- **Gate 2, analysis plan (04):** the human approved the plan with decisions on check 3, the labelling scope, the second matching stage, the permutation null, the frozen mapping table and a pilot stop with a hand check (`workflow/04_analysis_plan.md`, "Human decisions at Gate 2").
- **Gate 2, amendment 1 (04):** after the run stopped at the scope cap (section 4), the human raised the cap, added the media type to the title key and fixed the order of the matching stages (`workflow/04_analysis_plan.md`, "Gate 2, amendment 1").
- **Pilot check (05):** the pilot gate was an AI first pass. The human did not open the IMDb pages and accepted the AI check as the gate, "knowing it is weaker evidence than a hand check" (`workflow/05_pilot_check`). Match accuracy in the full labelled set therefore rests on that AI check, which is listed as a limit.
- **Insights revised after the critique (07):** the human revised `07_insights.md` after reading the 08 critique (commit `07-insights: revise after critique`). The answers to each critique point are in `workflow/09_recommendations.md`.

## 4. What the process caught

- **(a) Research claims that the sources did not support.** The human opened the sources cited in `01_research.md`. One claim about 2026 revenue guidance is not stated by the cited pages, and the link behind a shareholder-letter claim returns 404. Both are marked "Do not use" in `workflow/01_research_review.md`, and facts from them are not used unless confirmed in a primary source.
- **(b) A stop at the labelling-scope cap in step 05.** All three scope targets (90%, 85%, 80% of hours) exceeded the cap set in the plan, so the analyst stopped and asked instead of continuing (`workflow/05a_scope_stop.md`). The human then amended the plan (section 3). The run stopped a second time at the pilot hand check, as the plan required (`workflow/05b_pilot_stop.md`).
- **(c) The guard hook blocked a command.** `.claude/hooks/guard.py` rejects commands that contain the human approval phrase, because that line in the analysis plan is written by the human only. "During the review of the first analysis plan (step 04), the main Claude Code session ran a verification command that contained the human approval phrase. The guard hook blocked it with the message 'guard: blocked: the human approval line is written by the human only; do not put it in commands'. The session stopped without retrying or bypassing, and the check was redone without that phrase."
- **(d) Why the genre source changed from TMDB to IMDb.** The amendment records that the IMDb datasets need no API key or account, that the files stay outside the repository, and that use is personal and non-commercial with only aggregates published (`workflow/03_data_plan.md`). The Gate 2 amendment adds that the earlier scope cap was set when labels were to come from an API with call costs, and that with local IMDb files the cost is compute only (`workflow/04_analysis_plan.md`).

## 5. Limits

Summarised from `workflow/07_insights.md`, `workflow/06_validation.md` and `workflow/08_critique.md`.

- **Rule power:** the rule is hard to pass even by chance. Across all 5,040 orderings of the seven half-years, none passes at 2 pp and 24 pass at 1.5 pp (0.48%). Not passing says little about whether a smaller seasonal effect exists. I did not run a power test with a planted pattern.
- **Genre groups are coarse:** the fixed priority table gives 57.0% of labelled hours a group different from the first IMDb genre. Drama's average share is 4.88% while Crime & Thriller's is 30.94%, so a large catch-all group may hide opposite movements. No alternative mapping was run.
- **Matching:** 725 keys were ambiguous and 668 of them were settled by "most votes", which favours popular works. They were not checked by hand. The pilot match check was an AI first pass.
- **Coverage:** unlabelled hours rise from 3.08% to 4.49% of in-scope hours. Titles below Netflix's listing threshold are missing, and shares reflect what Netflix released and licensed, not only what viewers wanted. Only seven half-years are available.
- **Validation is not fully independent:** the validator reused the analyst's cleaning, title-key and IMDb matching code. Only the steps after the hours matrix were recomputed independently. A simple 400-key re-match agreed in 351 of 358 cases (98.0%) but shares the "most votes" logic.
- **Check 2 cannot separate two readings:** removing the top 10 titles per half-year cannot tell "big titles add noise" from "big titles are scheduled in the same half each year" (`workflow/07_insights.md`, I2; `workflow/08_critique.md`).
- **Single observation:** the Sci-Fi & Fantasy rise (+4.86 pp, H1 to H2 2025) coincides with Stranger Things and Wednesday. I have not shown that big titles drive genre shifts in general (I2).
- **A weak lead, not a finding:** Sci-Fi & Fantasy's mean aligned shift in check 1 is 1.85 pp, bootstrap 95% interval [0.33, 3.46]. The interval resamples titles, not years, and rests on one large jump (I1).
- **Not independently reproduced by the human:** I did not reproduce the key numbers myself and rely on the validator's recomputation (`workflow/07_insights.md`, Verification note).

## 6. Dated prediction

Written on 2026-11-12 (`workflow/09_recommendations.md`, R1, KPI):

- **Prediction:** for each tested genre group, the H2 2026 share equals the H1 2026 share within 2 pp (same mapping and scope rules).
- **Scoring plan:** when Netflix's first annual report is published (expected Q1 2027), derive H2 2026 hours by title if the report allows it, and compute the absolute difference per genre group. Success means all tested groups are within 2 pp. Partial means some groups are outside, and I report which groups moved.
- **Not scorable case:** if H2 2026 cannot be derived from the annual report, the KPI is not scorable. This was stated in advance.
- **Risk:** the KPI can fail simply because the 2026 slate differs, not because the baseline idea is wrong (R1).

## 7. How to reproduce

Raw data is not in this repo (see `data_manifest.json` for names, row counts, checksums and source URLs).

1. Set up the environment from the repo root: Python 3.12, `pip install -r requirements.txt`.
2. Get the external files listed in `data_manifest.json`: the seven Netflix What We Watched report files (H1 2023 to H1 2026) and the IMDb files `title.basics.tsv.gz`, `title.ratings.tsv.gz` and `title.akas.tsv.gz`. They are stored outside the repo, see `data_manifest.json`. The code reads them from the folders set in `pipeline/load.py` (`NETFLIX_DIR`, `IMDB_DIR`). Do not commit them.
3. The frozen genre mapping is `config/genre_mapping.csv`. The `full` stage refuses to run without the pilot check file `workflow/05_pilot_check`.
4. From this folder, run: `MPLBACKEND=Agg python main.py full` (stages in `main.py`: `manifest`, `pilot`, `full`). The log is `outputs/q1/full_run.log`.
5. Run tests: `pytest -q tests`. The validation tests that read the raw files need the external files from step 2.

## 8. Data sources and terms

- **Netflix What We Watched reports** (seven half-year files, H1 2023 to H1 2026). Source URLs are in `data_manifest.json`. Terms: "No license stated; raw files are not redistributed" (checked 2026-11-12, `workflow/03_data_plan.md`). Only aggregates are shared.
- **IMDb Non-Commercial Datasets** (`title.basics`, `title.ratings`, `title.akas`), used only to label genres. Source URLs are in `data_manifest.json`. The manifest records the terms as personal, non-commercial use with only aggregates published.
- **IMDb attribution notice:** Genre labels use data from the IMDb Non-Commercial Datasets (https://developer.imdb.com/non-commercial-datasets/), used here for personal, non-commercial purposes. Only aggregated results are published.
- Raw data of both sources is not in this repo. Only aggregated results are (`outputs/q1/`, `outputs/profile/`).

## 9. Not done

Listed in `workflow/09_recommendations.md` and `workflow/07_insights.md`:

- A power test with a planted seasonal pattern.
- An alternative genre mapping.
- A per-half scope instead of the fixed union scope.
- Hand checks of the ambiguous matches.
- Reproduction of the key numbers by the human.

## Decisions I made

- **Company and data:** I wanted a real company and recent, company-published data. I chose Netflix's What We Watched reports (seven half-years, H1 2023 to H1 2026).
- **Decision and question:** I chose the decision (which genres a content planner should strengthen in the H2 slate) and the question (do genre shares of viewing hours alternate by half-year). I fixed the rule before the analysis: the same alternating direction in all six transitions, by at least 2 percentage points (a threshold Claude recommended and I accepted), for genres with at least 5% average share, in three checks (all titles, without the top 10 titles, new vs carried-over titles).
- **Genre source:** I moved from TMDB to the IMDb non-commercial datasets because I did not want to create an API key. Local files pinned by checksum also made the labelling reproducible.
- **Genre mapping:** I committed a priority-ordered mapping table (drafted by Claude, reviewed by me) before any genre share was computed.
- **Scope:** after seeing the scope sizes (7,342 / 5,548 / 4,287 keys) and before any label or genre share existed, I raised the key cap from 3,000 to 4,500 on Claude's recommendation, so the 80% target could be used.
- **Shortcuts I chose, knowing the cost:** I accepted an AI first pass for the pilot match check, did not reproduce the key numbers myself, and skipped step 10 because there was no validated effect to model.

## What AI did

Based on `git log` and the `Author:` line of each file:

- **researcher** wrote the company and dataset research (`workflow/01_research.md`) and the data-feasibility check with a GO/NO-GO verdict (`workflow/03_data_plan.md`).
- **question-coach** gave feedback on the human's questions without rewriting them (`workflow/02_questions_feedback.md`).
- **analyst** wrote the analysis plan twice (once for TMDB, once after the IMDb amendment) and then executed the approved plan: data cleaning, IMDb matching, the three checks, bootstrap, permutation test and charts. It stopped at the scope cap and at the pilot hand check, as the plan required (`workflow/04_analysis_plan.md`, `workflow/05_analysis.md`, `workflow/05a_scope_stop.md`, `workflow/05b_pilot_stop.md`, `pipeline/`, `outputs/q1/`).
- **validator** recomputed the analyst's numbers with its own code and wrote the PASS/FAIL table and tests (`workflow/06_validation.md`, `tests/test_validation_*.py`).
- **critic** argued against the human's insights (`workflow/08_critique.md`).
- **main session** wrote the data-profile code and summary for the seven source reports (`pipeline/profile_reports.py`, `workflow/01b_data_profile.md`, `outputs/profile/`, author `ai/main-session`), started the sub-agents, checked each output and made the commits.
- **Writing notes:** the notes at the end of `07_insights.md` and `09_recommendations.md` state that those drafts were prepared by Claude in chat from the validated results and the human's own conclusions, and were reviewed by the human before committing.
- Step 10 (impact-modeler) was not run.

## Where AI critique changed my view

- The critic (08) agreed that the numbers were right but challenged how I read them. I accepted most points: the rule is strict, so "none found" is weak evidence; the genre groups are coarse; my claim in I2 about big titles rested on one example, so I reduced it to a single observation; and "recomputed independently" was too strong because the validator reused the analyst's matching code.
- I added a weaker lead the critic pointed out to my insights: the mean aligned shift for Sci-Fi & Fantasy (1.85 pp, interval 0.33 to 3.46). It is not a pass under my pre-set rule.
- I partly rejected one objection: the small "new" stratum does not decide the result, because check 1 alone already fails at all three thresholds.
- I kept the baseline recommendation but marked it provisional and attached a dated prediction to it.
- Full answers, point by point: `workflow/09_recommendations.md`. Critique: `workflow/08_critique.md`. Revised insights: `workflow/07_insights.md`.
