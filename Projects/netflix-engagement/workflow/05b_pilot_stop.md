Author: ai/analyst

# 05 Analysis: Netflix engagement (as-of 2026-11-12)

Status: STOPPED AT THE PILOT, as the approved plan requires. The pilot table (30 rows) is written and awaits the human hand check, to be recorded in `workflow/05_pilot_check.md`. Full-scope labelling, genre shares, the three checks, bootstrap, permutation test and charts were NOT run. Nothing from Q1 has been answered.

Gate check: `04_analysis_plan.md` ends with one `Approved: human` line after the Gate 2 decisions and amendment 1 sections; position and wording look normal. The frozen mapping `config/genre_mapping.csv` exists (commits a69b5e8, ace1ab2, both before any pilot or share). I did not edit it. Every distinct genre value in title.basics is in the mapping (28 values, no missing; log `outputs/q1/pilot_run.log`).

## Environment and reproducibility
- Python 3.12 (root .venv); pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, openpyxl 3.1.5, matplotlib 3.10.9 (versions as printed in the earlier run, 05a_scope_stop.md; same venv).
- Seed 42 (pilot sampling only: 15 tagged and 15 untagged keys, numpy default_rng).
- Run: `MPLBACKEND=Agg python main.py pilot` in the project folder. Log: `outputs/q1/pilot_run.log`. Tests: `pytest -q tests/test_clean_label.py tests/test_profile_reports.py`, 20 passed (`outputs/q1/pytest.log`).
- Code changed in this run: `pipeline/clean.py` (type in key, collision report, `id_col`), `pipeline/label.py` (all-segment stage 1, then stage 2, multi-segment preference), `main.py` (cap 4,500, typed key ids), `tests/test_clean_label.py` (3 new tests). IMDb manifest entries were recorded in the earlier run (`outputs/q1/manifest_imdb.log`, `data_manifest.json`).

## Amendment 1 as implemented
1. Cap raised to 4,500 unique keys; targets tried 90%, 85%, 80%.
2. Key = (cleaned title, media type). H1 2023 type is taken from the H2 2023 file when the cleaned title appears there with exactly one type, else "unknown" (matched as in P3).
3. Tagged titles: stage 1 (title.basics) over all segments first; stage 2 (title.akas) only if no segment gives a stage 1 candidate after type and year filters. Candidates are pooled; a candidate found by more than one segment is preferred, then most votes, then lowest tconst. `segments_matched` and `tie_break` (`multi_segment`, `votes`, `tconst`, `none`) are recorded per key.
4. akas is read in 2,000,000-row chunks and only rows whose normalised title is in the pilot's needed set are kept (60 hits). For the full scope the needed set will be the in-scope keys.
5. New / carried-over for H2 2023 by cleaned title against H1 2023: not implemented yet (belongs to the check 3 stage, after the pilot check).

## Movie/show key collisions (reported before the pilot, as required)
Evidence: `outputs/q1/clean_log.json` (key `collisions_before_type_in_key`), `outputs/q1/collisions_top20.csv`, `outputs/q1/pilot_run.log`. "Before" = title-only key, using the sheet's movie/show label; H1 2023 rows have no label so they cannot show a collision in H1 2023.
| measure | before (title only) | after (type in key) |
|---|---|---|
| unique keys, all halves, no scope | 25,849 | collisions become separate keys; unique typed keys not logged outside the scope |
| (key, half) pairs with both film and series hours | 767 | 0 by construction |
| share of listed-title hours in those pairs | 3.64% | 0 |
| keys with both film and series hours in any half | 411 | 0 by construction |
| share of listed-title hours in those 411 keys | 5.80% | 0 |
| scope union at 90 / 85 / 80% | 7,342 / 5,548 / 4,287 | 7,523 / 5,683 / 4,398 |
| H1 2023 rows typed from H2 2023 / left unknown | n/a | 13,767 / 4,447 |
| keys with type "unknown" (all halves) | n/a | 3,836 |

The 20 largest collisions by hours (before), all hours dominated by one type: S.W.A.T. (2.68e9 h, film 1.59e7), The Rookie, The Resident, The Lincoln Lawyer, Love Is Blind, The Flash, Lost, Outlander, Animal Kingdom, The Diplomat, The Gentlemen, Homeland, The Smurfs, Parenthood, Warrior, Ragnarok, One Day, The Equalizer (film 1.87e8, series 1.24e8), Man on Fire (film 1.13e8, series 2.24e8), Van Helsing. Full numbers in `collisions_top20.csv`. Most are a series plus a small same-name film; the type split is therefore real for the large ones, but the 3,836 unknown-type keys (H1 2023 only titles) cannot be split.

## P4 scope (hours only, set before any label)
Evidence: `outputs/q1/scope_candidates.csv`, `outputs/q1/scope.json`.
| target | union keys | H1 23 | H2 23 | H1 24 | H2 24 | H1 25 | H2 25 | H1 26 |
|---|---|---|---|---|---|---|---|---|
| 90% | 7,523 | 3,033 | 3,024 | 2,941 | 2,818 | 2,964 | 3,138 | 3,296 |
| 85% | 5,683 | 2,169 | 2,178 | 2,105 | 2,023 | 2,115 | 2,248 | 2,345 |
| 80% | 4,398 | 1,600 | 1,617 | 1,559 | 1,511 | 1,565 | 1,663 | 1,710 |
Chosen: 80%, 4,398 unique keys (at most 4,500, so no stop). Adding the type moved the 80% union from 4,287 to 4,398, still under the cap. Top-10 per half are inside the scope by construction (they are the largest keys).

## P1/P2 cleaning (evidence `outputs/q1/clean_log.json`)
Rows read 115,956; Other Movies/Shows rows 4 (excluded from keys, kept for the all-hours total); dropped for missing hours or title 0; zero or negative hours none; whole-row duplicates 0; rows merged by key 9,111 keys with more than one row (20,611 rows absorbed); H1 2023 trailing-number resolutions 200.

## P5 pilot (30 keys, seed 42)
Evidence: `outputs/q1/pilot_table.csv` (columns include key, Netflix title, tagged/untagged, type used, year source, matched IMDb title, IMDb type, year, genres, group, stage, segments matched, candidates, tie-break), log `outputs/q1/pilot_run.log`. Sampled from pools of 1,401 tagged and 2,997 untagged in-scope keys.
- Match rate 30/30 = 100% (tagged 15/15, untagged 15/15); labelled 30/30. The 85% gate is passed.
- Stage: 28 matched in stage 1, 2 in stage 2 (akas: "suzuki=bakudan" to Bomb 2025, "the price of glory" to Ventino. El precio de la gloria 2023). Tie-break "none" for all 30, meaning the pilot had one candidate each and tests none of the ambiguity rules. A 100% match rate here says that a candidate was found, not that it is right.
- My own check (the human check is the authority): I agree with 28 rows (same title, matching type and plausible year). I mark rows 7 (suzuki=bakudan to Bomb, matched only through akas on the second segment) and 9 (the price of glory to Ventino. El precio de la gloria, akas) as "plausible, please verify". I disagree with none on the evidence in the table, but I cannot verify content outside it.
- Genre grouping to look at during the hand check: priority rules turn family tags into "Kids & Family" for Beauty and Mr. Romantic (Drama,Family,Romance), Mr. Car and the Knights Templar and The Call of the Wild, and make Escape Room (Action,Adventure,Horror) "Crime & Thriller" and The Queenstown Kings (Drama,Sport) "Action & Adventure". These follow the frozen table; they are examples of the coarse label the plan warns about, not changes I made.

## Not done (waiting for the human)
Full-scope labelling and its coverage / bias report, check 1 to 3, bootstrap, permutation test, sensitivity, charts, H2 2026 table. Continue only after `workflow/05_pilot_check.md` exists.

## Limitations carried from the plan
Shares reflect Netflix's own slate, not viewer demand. Only seven half-years. IMDb primary genre by priority table is a coarse label. The H2 2026 prediction may not be scorable. The "new" stratum includes titles that first crossed the report's listing threshold, not only newly released ones; hours are reported at coarse resolution with many ties. Additional: 3,836 keys have unknown type (H1 2023-only titles), so same-name film and series pairs among them are not separated.
