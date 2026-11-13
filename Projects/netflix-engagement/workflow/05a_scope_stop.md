Author: ai/analyst

# 05 Analysis: Netflix engagement (as-of 2026-11-12)

Status: STOPPED at plan step P4 (labelling scope). The stop condition "even the 80% target exceeds 3,000 unique keys" triggered. No genre has been matched, no pilot table exists, and no genre share was computed. Nothing from Q1 has been answered.

Gate check: `04_analysis_plan.md` ends with a single `Approved: human` line after the Gate 2 decisions section; wording and position look normal. The frozen mapping `config/genre_mapping.csv` was committed before this run (git log: a69b5e8 on 2026-11-12 19:05, rewritten for IMDb names in ace1ab2 at 19:23). I did not edit it.

## Environment and reproducibility
- Python 3.12 (root .venv); pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, openpyxl 3.1.5, matplotlib 3.10.9 (printed by the version command in this session).
- Random seed 42 (used only for pilot sampling, not reached).
- Run: `MPLBACKEND=Agg ../../.venv/bin/python main.py pilot` from the project folder. Log: `outputs/q1/pilot_run.log`.
- Code: `pipeline/load.py`, `pipeline/clean.py`, `pipeline/label.py`, `main.py`; tests `tests/test_clean_label.py` (10 tests) plus the existing profile tests, 17 passed in total (`pytest -q tests/test_clean_label.py tests/test_profile_reports.py`).

## Done
### IMDb files recorded in data_manifest.json
Script `main.py manifest` (`pipeline/load.py: record_imdb_manifest`), log `outputs/q1/manifest_imdb.log`:
| file | data rows | sha256 | file date |
|---|---|---|---|
| title.basics.tsv.gz | 12,953,566 | 0cc1480ce29cd313c18a83da6333757bc0e7c3aff7c3040d459213c0ad3f1ef6 | 2026-11-12 |
| title.ratings.tsv.gz | 1,731,454 | 50b091b46e73946f5e5de9acba86bc16fc6552cee90e7ef7ff2743645a7513f5 | 2026-11-12 |
| title.akas.tsv.gz | 60,353,877 | 72508408a4b45d16bd5c687d65fa80bb398e291d108f4fe108c6cfe3e17d7c77 | 2026-11-12 |
Source URLs are https://datasets.imdbws.com/<file>. The download date is the file modification date, as for the Netflix entries.

### P1/P2 cleaning (evidence: `outputs/q1/clean_log.json`, `outputs/q1/pilot_run.log`)
- Rows read: 115,956 (matches the sum of the manifest row counts). Other Movies/Other Shows rows: 4 (H2 2025 and H1 2026), excluded from keys and kept for the all-hours total. Rows dropped for missing hours or title: 0. No zero or negative hours. Whole-row duplicates: 0.
- Rows merged by key within a half (seasons to one title): 9,502 keys had more than one row; 21,378 rows were absorbed.
- Movie/series key collisions: 767 (key, half) pairs within a half and 411 keys across halves. Keys are typed by the larger of film vs series hours.
- H1 2023 rows with a trailing number (for example "Stranger Things 4") resolved against series keys of other halves: 200.

### P4 scope, hours only (evidence: `outputs/q1/scope_candidates.csv`)
Keys per half needed to reach the cumulative share of listed-title hours, and the union over the seven halves:
| target | union of keys | H1 23 | H2 23 | H1 24 | H2 24 | H1 25 | H2 25 | H1 26 |
|---|---|---|---|---|---|---|---|---|
| 90% | 7,342 | 3,033 | 2,991 | 2,904 | 2,784 | 2,931 | 3,106 | 3,264 |
| 85% | 5,548 | 2,169 | 2,154 | 2,076 | 2,000 | 2,094 | 2,227 | 2,326 |
| 80% | 4,287 | 1,600 | 1,599 | 1,538 | 1,496 | 1,553 | 1,650 | 1,698 |
All three exceed the 3,000-key cap, so the plan says stop and ask.

## Not done (blocked)
Genre-value check against the mapping, pilot sampling and matching (30 keys), `outputs/q1/pilot_table.csv`, full labelling, coverage report, Q1 checks, bootstrap, permutation test and charts. None of these exist.

## Decision needed from the human
The cap and the targets are fixed by the plan, so I did not pick a workaround. Options, for the human to choose (none is approved):
1. Raise the cap (for example to 4,500, which would admit the 80% target at 4,287 keys).
2. Add a lower target or a fixed per-half rank cutoff (for example top N titles per half). I can print the union size for any such rule, hours only, in seconds.
3. Keep the cap and accept that the scope reaches less than 80% of hours in each half.
Note for the choice: the matching and the 10% unlabelled-hours coverage rule are measured inside the scope, so a smaller scope lowers the labelling effort but also the share of total viewing the genre shares describe.

## Suggestions outside the plan (not run)
- The 767 within-half movie/series collisions are many for a key built only from the title text. If the human wants them examined (for example whether they are real same-name film and series pairs), that is an extra diagnostic.
- Match rate on akas (60 million rows) takes a few minutes per pass; the plan's stage 2 is still affordable at 4,000 to 5,000 keys if the lookup set is built once.

## Limitations carried from the plan
Shares reflect Netflix's own slate, not viewer demand. Only seven half-years. IMDb primary genre by priority table is a coarse label. The H2 2026 prediction may not be scorable. The "new" stratum includes titles that first crossed the report's listing threshold, not only newly released ones; the hours are reported at coarse resolution with many ties.
