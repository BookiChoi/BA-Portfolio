# NYC taxi and ride-hail trips: where to guide drivers, and what congestion pricing changed

## Summary

- **Company:** NYC Taxi & Limousine Commission (TLC) public trip records: yellow taxis and high-volume for-hire vehicles (HVFHV, Uber and Lyft), analysed separately.
- **Business question (one line):** Four questions for fleet operations and business development (`workflow/02_questions.md`): where pickups concentrate by part of the day (Q1), where airport trips end (Q2), how the night share of trips differs between weekdays and weekends (Q3), and whether the share of trips touching the congestion pricing zone fell after pricing started (Q4).
- **Key finding (one line):** Yellow pickups are concentrated (36 zones cover 80%) and HVFHV pickups are not (128 zones); the zone share fell after pricing for both services by more than the earlier baseline change, but the critique (08) shows that this design cannot separate a fee effect from trend, season or data changes (`workflow/07_insights.md`, I1 and I4).

## How to reproduce

Raw data is not in this repo (`data_manifest.json` lists source URLs, download date, row counts and checksums).

1. Set up the environment from the repo root (Python 3.12, `pip install -r requirements.txt`). The neighbouring-zone step also needs `geopandas`, which is not in `requirements.txt` yet (see "Not done").
2. Put the data in `Projects/nyc-congestion-pricing/data/`: 60 monthly Parquet files (30 yellow, 30 HVFHV), the taxi zone lookup, the MTA "Central Business District Taxi Zones" list and the taxi zones shapefile. The files are named as in the source URLs in `data_manifest.json`. Do not commit them.
3. From the project folder, run: `MPLBACKEND=Agg python main.py all` (`FORCE_AGG=1` rebuilds the per-file aggregates in `outputs/cache/`).
4. Run tests: `pytest -q` (analysis code) and `pytest -q tests/test_validation_recompute.py` (validator checks).

## Who did what

Commit prefixes are copied from `git log`. The owner is taken from the `Author:` line of each document.

| Stage | Owner | File | Commit |
|---|---|---|---|
| 00 Brief | human | `workflow/00_brief.md` | `[PROJECT] ... 00 brief` (scaffold: `00-init`) |
| 01 Research | AI (researcher) | `workflow/01_research.md` | `[AI-PROJECT] ... 01-research` |
| 02 Business questions | human | `workflow/02_questions.md` | `[PROJECT] ... 02 questions` (three commits) |
| 02 Question feedback | AI (question-coach) | `workflow/02_questions_feedback.md` | `[AI-PROJECT] ... 02-feedback` |
| 03 Data feasibility (GO/NO-GO) | AI (researcher) | `workflow/03_data_plan.md` | `[AI-PROJECT] ... 03-data-plan` |
| 03 Approval and decisions | human | `workflow/03_data_plan.md` | `[PROJECT] ... 03 data plan approved` |
| 04 Analysis plan | AI (analyst) | `workflow/04_analysis_plan.md` | `[AI-PROJECT] ... 04-analysis-plan` |
| 04 Plan approval and decisions | human | `workflow/04_analysis_plan.md` | `[PROJECT] ... 04 plan approved` |
| 05 Analysis execution | AI (analyst) | `workflow/05_analysis.md`, `pipeline/`, `main.py`, `tests/test_analyze.py`, `outputs/` | `[AI-PROJECT] ... 05-analysis` |
| 05 Review note | human | `workflow/05a_human_review.md` | `[PROJECT] ... 05 review` |
| 06 Validation (PASS/FAIL) | AI (validator) | `workflow/06_validation.md`, `workflow/logs/validation_*`, `tests/test_validation_recompute.py` | `[AI-PROJECT] ... 06-validation` |
| 07 Insights | human | `workflow/07_insights.md` | `[PROJECT] ... 07 insights`, `07 amendment` |
| 08 Critique | AI (critic) | `workflow/08_critique.md` | `[AI-PROJECT] ... 08-critique` |
| 09 Recommendations | human | `workflow/09_recommendations.md` | `[PROJECT] ... 09 recommendations`, `09 amendment` |
| 10 Impact forecast | AI (impact-modeler) | `workflow/10_impact.md`, `workflow/10_impact_assumptions.json`, `pipeline/impact_model.py`, `outputs/impact_*` | `[AI-PROJECT] ... 10-impact` |

## Human gates and decisions

- **Gate 1, data plan (03):** the researcher's verdict was GO (conditional). I approved it after the data was in place and the zone lists were fixed (`workflow/03_data_plan.md`, "Human decisions at Gate 1").
- **Gate 2, analysis plan (04):** I approved the plan with eight decisions and three open items (the zone lists, the rule for neighbouring zones, and terms of use) (`workflow/04_analysis_plan.md`, "Human decisions at Gate 2 (2026-11-13)").
- **Review after the run (05):** the plan's wording for Q3 sensitivity S3 (what counts as a weekend night) contradicted itself. The analyst ran and reported both readings. I chose the intended reading and kept the literal one as a reported alternative (`workflow/05a_human_review.md`).
- **Key numbers (07):** I reproduced only the Q1 yellow numbers myself (valid trips 46,415,189; n50 17; n80 36). The other numbers rely on the validator (`workflow/07_insights.md`, Notes).
- **After the critique and the forecast:** I recorded corrections in an amendment at the end of `workflow/07_insights.md` (after 08) and of `workflow/09_recommendations.md` (after 10).

## What the process caught

- **A contradictory plan sentence (S3).** The analyst did not pick a reading silently; it ran both and said so. The validator reproduced both result sets exactly.
- **A mislabelled stability number (I1).** My insight called the Jaccard overlap "month-to-month". The critic and `05_analysis.md` show it compares each month with a full-period list that contains that month, so it is in-sample. Corrected in the 07 amendment.
- **A pilot that could not test its own rule (R1).** The impact forecast showed that 50 drivers per group cannot detect an effect near the +3% success line. The pilot was reframed as a feasibility study in the 09 amendment.
- **An unclear reading in R2.** The forecast showed that the base case misses the 2 pp line if the shift applies to users only. The reading and the gap are recorded in the 09 amendment.
- **Validation found no number to send back.** 775 checks, 0 mismatches. It also measured duplicates (1.14% of yellow rows; removing them moves the Q4 yellow margin from +1.81 to +1.89 pp).

## Limits

Summarised from `workflow/07_insights.md`, `06_validation.md`, `08_critique.md` and `10_impact.md`.

- **Q4 is a before/after comparison.** One baseline year pair; the HVFHV baseline is already falling (-1.69 pp); the yellow drop is concentrated in January-May 2026; 2025 is not in the comparison; a column was added to yellow files for 2026-06 to 2026-09 in the same months the yellow share rises back, and a data change was not ruled out. "No obvious new hotspot" rests on top-15 single-zone changes without a noise reference.
- **Q3 is about shares, not counts.** A higher weekend night share can come from fewer daytime trips. The time zone of the timestamps was assumed, not verified. The bootstrap resamples month x day-of-week cells, not month x day type as in the plan.
- **Q1 and Q2.** The list stability is in-sample, "workable" was never measured, and the yellow (50%) and HVFHV (40%) coverage targets differ. The Q2 comparison uses the top-5 pickup share as a benchmark (low for HVFHV); same-airport trips are kept and 13-20% of HVFHV airport trips have an unknown destination.
- **Zone IDs.** That zone IDs keep the same meaning from 2023 to 2026 is not verifiable. The validator checked data behind the charts, not the PNG files.
- **Terms of use.** No explicit licence or terms were found on the TLC page (checked 2026-11-13, recorded in `data_manifest.json`).
- **Forecast.** The effects in 09 are my judgments, not data. Five unsourced values in `10_impact.md` are marked `modeler_placeholder`. All forecast results are relative (%, pp, drivers); there is no earnings or waiting-time data.
- **Reproduction.** I reproduced only the Q1 yellow numbers myself.

## Data sources and terms

- **TLC Trip Record Data:** monthly Parquet files for yellow taxis and HVFHV (Jan-Sep 2023, Jan-Sep 2024, Oct 2025 - Sep 2026), plus the taxi zone lookup and the taxi zones shapefile. URLs and checksums are in `data_manifest.json`. Terms: not found (see Limits).
- **MTA "Central Business District Taxi Zones"** list (38 taxi zone IDs), downloaded 2026-11-13, used as the definition of the congestion pricing zone.
- Raw data of all sources is not in this repo; only code, small aggregated tables and charts (`outputs/`) and the workflow documents are.

## Not done

- A time-split test of the yellow zone list; night trip counts per day by day type; the 2025 data and placebo year pairs for Q4; a sensitivity for same-airport trips and unknown destinations in Q2.
- The pilots themselves: the recommendations in `workflow/09_recommendations.md` are plans, and no pilot has run.
- Reproduction of the HVFHV, Q2, Q3 and Q4 key numbers by me.
- Adding `geopandas` to `requirements.txt`; fixing the overlapping chart titles in the Q1 heat tables; keeping `outputs/cache/` and `workflow/logs/validation_cache/` out of the repo.

## Decisions I made

- **Dataset:** I chose the NYC TLC trip records over the older Olist dataset because the data is recent (through September 2026) and shows real human behaviour.
- **Questions and decision makers:** I wrote four questions from my own curiosity (busiest areas, concentration, weekday versus weekend, a possible new area) and tied each to a decision: fleet operations for Q1-Q3, operations and business development for Q4. I kept yellow taxis and HVFHV separate, and used the combined view only as supporting context.
- **Airport question:** I changed Q2 to look at where airport trips end, to see where passengers go.
- **Pre-set rules:** the decision rules were fixed before any result. Q4 compares the change after pricing with a 2023-2024 baseline, after the question coach pointed out a circular rule.
- **Data and zone lists:** I downloaded the 60 files myself and kept them out of git. I chose the MTA list as the definition of the pricing zone and fixed the airport IDs (Newark, JFK, LaGuardia) before the analysis.
- **Plan gate:** I approved the analysis plan with my decisions. I accepted Claude's recommendation for the neighbouring-zone rule (zones that touch the list, found with the taxi zones shapefile).
- **S3 reading:** I chose the intended reading and kept the literal one as a reported alternative.
- **Insights and recommendations:** I chose four insights and three recommendations. I dropped the airport-destination recommendation because the evidence was weak. The values in the assumption tables of `09_recommendations.md` were proposed by Claude and I accepted them, because I had no fleet data.
- **Shortcuts I chose, knowing the cost:** I reproduced only the Q1 yellow numbers, and I did not check the time zone or the zone ID meaning across years.

## What AI did

Based on `git log` and the `Author:` line of each file:

- **researcher** wrote the company and dataset research (`workflow/01_research.md`) and the data-feasibility check with a GO/NO-GO verdict (`workflow/03_data_plan.md`).
- **question-coach** gave feedback on my questions without rewriting them (`workflow/02_questions_feedback.md`).
- **analyst** wrote the analysis plan and then ran the approved plan on 60 monthly files: counts per zone and day part, bootstrap, Holm correction, regression, neighbouring-zone detection from the shapefile, and charts (`workflow/04_analysis_plan.md`, `workflow/05_analysis.md`, `pipeline/`, `outputs/`).
- **validator** recomputed the analyst's numbers by a different route (DuckDB SQL, its own bootstrap code and seeds) and wrote the PASS/FAIL tables, tests and extra sensitivity checks (`workflow/06_validation.md`, `workflow/logs/`, `tests/test_validation_recompute.py`).
- **critic** argued against my insights (`workflow/08_critique.md`).
- **impact-modeler** turned my assumptions into scenarios, power calculations and experiment designs (`workflow/10_impact.md`, `workflow/10_impact_assumptions.json`, `pipeline/impact_model.py`).
- **main session** started the sub-agents, checked each output and made the `[AI-PROJECT]` commits.
- **Claude in chat** (the design and review chat, not a sub-agent) helped me draft `workflow/02_questions.md`, `05a_human_review.md`, `07_insights.md`, `09_recommendations.md` and their amendments, and this README, from my own decisions. The notes at the end of those files say so. I chose the claims and reviewed the text.

## Where AI critique changed my view

- **Question coach (02):** I revised the questions after its feedback (commit `b9ab3dc`), including how the Q4 decision rule is defined.
- **Critic (08):** I accepted most of its points: the list stability was in-sample and mislabelled; "workable" was never measured; the airport benchmark and the unknown destinations weaken the Q2 contrast; the Q3 result is a share, not a count; the Q4 timing and the unverified schema change weaken a policy reading; "no new hotspot" was too strong. I recorded them in the 07 amendment.
- **One objection I partly rejected:** the critic said the Q3 headline depends on the S3 reading I chose. It does not: the primary result (13.12 pp for yellow, 10.16 pp for HVFHV) uses the pickup date; S3 is a sensitivity check. I added the S3 detail and the 11-of-12 result for HVFHV to the amendment.
- **Impact forecast (10):** it changed my plan more than I expected. My first pilot (50 drivers per group, +3% rule) could not test its own rule, so I reframed it as a feasibility study. It also showed that the R2 target is missed in the base case if the shift applies to users only; I recorded the gap and did not move the target. It also showed that, if the earlier decline continued, the HVFHV change left after removing the trend would be small and uncertain, which supports running the follow-up (R3) before any zone-entry decision.
- Full answers: `workflow/07_insights.md` (amendment), `workflow/08_critique.md`, `workflow/09_recommendations.md` (amendment).
