Author: ai/analyst

# 05 Analysis: Netflix engagement (as-of 2026-11-12)

Status: complete for Q1, the only question. The approved plan (`04_analysis_plan.md`, with Gate 2 decisions and amendment 1) was run from the pilot gate onward. No insights or recommendations are written here; those are the human's.

Headline of the numbers (not an interpretation): no eligible genre passes the pre-registered rule at 2 pp, or at 1.5 pp or 3 pp. Evidence: `outputs/q1/genre_results.csv`, `outputs/q1/results.json`, run log `outputs/q1/full_run.log`.

## Gate check and pilot
- `04_analysis_plan.md` ends with a single `Approved: human` line after the amendment sections; position and wording look normal.
- Pilot check: `workflow/05_pilot_check` (human, 2026-11-12) records 30/30 correct against a 27/30 rule, so the gate is passed and I continued. Caveat the human wrote and I carry: the 30/30 comes from an AI check (same model family as the matching agent), not from the human opening IMDb pages. The accuracy of the full labelled set rests on that weaker evidence (limitation L1).
- The pilot check noted that the priority table gives coarse groups; its share in the full set is reported below (section "Group coarseness").

## Environment and reproducibility
- Python 3.12.14 (root `.venv`), pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, openpyxl 3.1.5, matplotlib 3.10.9 (printed by an executed one-line script in this session). scipy is installed but not used by the analysis code.
- Seed 42 for the bootstrap (numpy `default_rng`, 2,000 replicates) and the pilot. The permutation tests are exact enumerations (5,040 and 720 orderings), so no seed.
- Run: `MPLBACKEND=Agg python main.py full` in the project folder; log `outputs/q1/full_run.log`. Tests: `pytest -q tests`, 29 passed (`outputs/q1/pytest_full.log`); `tests/test_analyze.py` is new (margins, check 3 transitions, NaN never passes, permutation counts, seeded cluster bootstrap, pair rule, Newcombe against a published example, new/carried masks).
- New code: `pipeline/analyze.py`, `pipeline/visualize.py`, `pipeline/q1_run.py`, `label.label_keys` in `pipeline/label.py`, stage `full` in `main.py`. Pilot-stage code was reused unchanged. The stage refuses to run without the pilot check file.
- No data files were written into the repo. Raw files stay in `~/Downloads/`; IMDb manifest entries were recorded earlier (`data_manifest.json`, `outputs/q1/manifest_imdb.log`).

## Scope and labelling (P4, P3)
Evidence: `outputs/q1/scope.json` (unchanged from the pilot run: 80% target, 4,398 keys, below the 4,500 cap, so no stop), `outputs/q1/full_run.log` line 2, `outputs/q1/results.json`.
- Decision taken where the plan was silent: the fixed scope is the union of 4,398 keys. A key in the union is counted in every half where it has hours, even in a half where it is below that half's 80% cut. In-scope hours per half therefore equal the hours of the union keys in that half (`in_scope_hours` in `outputs/q1/coverage_by_half.csv`). The alternative (per-half scope) was not run, since the plan does not contain it.
- Matched 4,146 of 4,398 keys (94.27%); labelled 4,145 (one matched title has only unmappable genres). Stage 1: 4,007 keys, stage 2 (akas): 139, no match: 252.
- Ambiguity: 725 keys had more than one candidate after the filters; tie-break used: votes 668, multi-segment preference 57, tconst 0 (the rest "none", which includes the 252 unmatched). The pilot did not test these rules (all 30 had one candidate), so the 725 ambiguous matches are the least verified part of the labelling.

## Coverage and bias (P5)
Evidence: `outputs/q1/coverage_by_half.csv`, `outputs/q1/match_rate.csv`, `outputs/q1/chart5_coverage_match.png`/`.csv`.
- Coverage rule: unlabelled hours are 3.08% to 4.49% of in-scope hours across the seven halves (maximum 4.49% in H1 2026), far below the 10% limit, so Q1 is NOT marked inconclusive by this rule.
- Labelled hours / in-scope hours: 96.92, 96.77, 96.35, 96.28, 96.76, 95.96, 95.51% (H1 2023 to H1 2026). Labelled hours / all listed hours (including the Other aggregates): 80.4 to 85.6%. Hours outside the scope are 11.5% to 17.0% of listed hours per half. Coverage drifts down slightly over time (4.49% unlabelled in H1 2026 vs 3.08% in H1 2023).
- Match rate by language tag (key counts, Wilson 95% CI): tagged 93.58% (1,311/1,401, CI 92.17 to 94.74), untagged 94.59% (2,835/2,997, CI 93.73 to 95.35). Difference tagged minus untagged -1.02 pp, Newcombe 95% CI -2.61 to +0.44 pp (labelled rate: -0.99 pp, CI -2.58 to +0.47).
- Per half, key-level labelled rate tagged minus untagged (Newcombe): -4.1 pp (CI -6.7 to -2.0) in H1 2023, -3.4 (-5.7 to -1.6), -2.9 (-5.0 to -1.2), -2.0 (-3.9 to -0.4), -2.2 (-3.9 to -0.6), -1.3 (-3.0 to +0.1), -0.9 (-2.5 to +0.5) in H1 2026. Interpretation made by me for the plan's "proportion differences": the Newcombe interval is applied to key counts. Hours-weighted coverage by tag is given as point values only (columns `labelled_over_inscope_pct_tagged/untagged` in the CSV, e.g. H1 2026: 94.47% vs 95.85%), because hours are not binomial counts.

## Group coarseness (requested in the pilot decision)
Evidence: `outputs/q1/results.json` (`group_differs_from_first_genre`). The priority table picks a group different from the group of the first-listed IMDb genre for 54.3% of labelled keys and 57.0% of labelled hours. This is a measure of how much the frozen priority rule, rather than the first-listed genre, drives the labels. The mapping was not changed.

## Q1: Does any genre alternate by half-year?
- Method: pre-registered direct computation (6 shifts, margin = smallest aligned shift in pp, pass at theta = 2 pp in the same direction on check 1, check 2, check 3 new and check 3 carried over), cluster bootstrap over title keys (2,000 replicates), max-statistic permutation test (alpha 0.05), pair rule, sensitivity at theta 1.5 and 3 and post-stratification by language tag.
- Eligible genres (mean check-1 share >= 5%): Documentary & Reality 6.21%, Kids & Family 5.78%, Animation 13.54%, Sci-Fi & Fantasy 9.56%, Crime & Thriller 30.94%, Action & Adventure 8.45%, Comedy & Romance 20.65%. Drama is below 5% (`mean_share_pct` in `results.json`).
- Charts (PNG + CSV beside each, in `outputs/q1/`): `chart1_share_lines`, `chart2_shift_bars`, `chart3_check_matrix`, `chart4a_perm_null_check1`, `chart4b_perm_null_all`, `chart5_coverage_match`. Chart 6 (H2 2026 prediction table) is not produced because nothing passes. Full per-genre numbers: `genre_results.csv`; shares of all genres and variants: `shares_all_variants.csv`; hours per variant: `variant_hours.csv`.

### Result by genre (pp; evidence `outputs/q1/genre_results.csv`, 95% cluster-bootstrap CI in brackets)
Direction = the direction with the larger genre margin. Check margins are in that direction. A pass needs all four margins >= 2.0.

| Genre | Dir | Check 1 | Check 2 | Check 3 new | Check 3 carried | Genre margin | Mean aligned shift (check 1) |
|---|---|---|---|---|---|---|---|
| Documentary & Reality | up | -0.62 [-2.33, 0.05] | -0.63 [-2.52, 0.09] | 0.40 [-5.34, 2.79] | -1.32 [-3.12, -0.47] | -1.32 [-5.02, -0.67] | -0.07 [-0.96, 0.84] |
| Kids & Family | down | -0.98 [-1.82, -0.42] | -1.13 [-2.72, -0.58] | -1.66 [-4.02, 0.02] | -0.99 [-1.89, -0.58] | -1.66 [-3.26, -0.42] | -0.33 [-0.73, 0.08] |
| Animation | up | -1.02 [-3.12, 0.07] | -0.67 [-2.22, -0.01] | -2.16 [-9.01, 1.03] | -1.25 [-3.37, -0.30] | -2.16 [-4.97, -0.85] | 0.14 [-0.82, 1.19] |
| Sci-Fi & Fantasy | up | 0.49 [-2.04, 1.12] | -0.54 [-2.80, 0.22] | -0.38 [-8.40, 3.92] | -0.05 [-2.04, 0.77] | -0.54 [-7.43, -0.29] | 1.85 [0.33, 3.46] |
| Crime & Thriller | up | -2.79 [-7.45, -1.13] | -1.75 [-5.01, 0.34] | -3.03 [-17.47, 3.11] | -3.49 [-7.98, -1.10] | -3.49 [-12.88, -2.50] | -0.80 [-2.93, 1.26] |
| Action & Adventure | down | -0.58 [-2.51, 0.61] | -0.76 [-2.79, 0.57] | 1.51 [-6.14, 4.09] | -1.31 [-3.17, -0.30] | -1.31 [-5.37, -0.53] | 0.67 [-0.44, 1.73] |
| Comedy & Romance | down | -2.76 [-7.21, 0.53] | -2.31 [-5.44, -0.12] | -3.87 [-12.38, 2.65] | -1.75 [-5.82, 0.45] | -3.87 [-10.55, -1.85] | 0.36 [-1.64, 2.62] |

- Passing genres at 2 pp: 0 of 7; findings after the pair rule: 0 (pair rule not applicable). Bootstrap pass fraction for every genre at theta 1.5, 2 and 3: 0.000 (`boot_pass_frac_theta_*` columns). Near misses within 0.05 pp of 2 pp: none (`results.json`, `near_misses_theta_2` empty).
- The six check-1 shifts per genre are in `genre_results.csv` (`shift_1`..`shift_6`) and `chart2_shift_bars.csv` with their bootstrap CIs. The largest single shifts are Sci-Fi & Fantasy +4.86 pp (H1 2025 to H2 2025) and -3.60 pp (H2 2025 to H1 2026), and Crime & Thriller -2.79 pp (H1 2023 to H2 2023) and +2.69 pp. These are single transitions, not a repeated pattern: Sci-Fi & Fantasy's check 1 margin is the smallest shift (0.49 pp).
- Check 3 detail (mean of the five aligned shifts d2..d6 in the genre's direction, pp): new stratum 2.03, 0.42, 0.81, 3.14, 2.02, 2.86, 3.49 and carried stratum -0.68, -0.54, -0.48, 1.81, -0.97, -0.19, 0.36, in the genre order of the table (`mean_aligned_shift_c3n_5trans`, `mean_aligned_shift_c3c_5trans`). The "new" stratum is small (1.6e10 to 2.0e10 hours per half versus 5.9e10 to 6.4e10 carried, `variant_hours.csv`) and its CIs are wide.
- Check 2: one top-10 cell is an unlabelled key (`top10_cells_unlabelled` = 1), so one half drops only nine labelled keys.

### Permutation test (supplementary; evidence `results.json`, `chart4a_*`, `chart4b_*`)
Statistic M = maximum over the seven eligible genres of the genre margin; the p-value is the share of orderings with M at least the observed M.
- Check 1 only, 5,040 orderings: observed M = +0.49 pp (Sci-Fi & Fantasy), p = 0.138. Orderings with any pass: 24 at theta 1.5 (0.48%), 0 at 2.0, 0 at 3.0.
- All checks, 720 orderings with H1 2023 fixed: observed M = -0.54 pp, p = 0.039. Orderings with any pass: 0 at 1.5, 2.0 and 3.0. Reading aid (a fact about the statistic, not an insight): the observed M is negative, so the observed data do not pass; the p-value says the observed M is higher than in 96% of re-orderings, which says only that most re-orderings are worse, since a four-way pass is hard to reach in any ordering. Per the Gate 2 decision, p is not read as evidence of a pass without a pass.
- Reference from the question: 2 x (1/2)^6 = 3.125% for one genre with six independent signs. Here the enumeration shows 0 of 5,040 orderings (check 1 only, 2 pp) have any pass across seven genres.

### Sensitivity (evidence `results.json`, `outputs/q1/sensitivity_poststrat.csv`)
- theta 1.5: no genre passes; theta 3: none. Passing genres 0 in all three.
- Post-stratification of check 1 by tagged/untagged coverage: no genre passes check 1 at 1.5, 2 or 3 pp, weighted or unweighted. Best weighted check-1 margins by genre (max of up/down): Kids & Family +0.13, Sci-Fi & Fantasy +0.50; the others are negative. Weighting changes margins by at most a few tenths of a pp (compare `check1_margin_*` with `check1_margin_unweighted_best`).

## One-line takeaway for Q1 (descriptive)
No eligible genre meets the pre-registered pass rule at any threshold tried; the best check-1 margin is 0.49 pp (Sci-Fi & Fantasy), and the best all-check margin is -0.54 pp.

## Limitations
- L1. Match accuracy in the full set rests on an AI-only pilot check (30 rows); 725 keys with several candidates were not individually checked.
- L2. Shares reflect Netflix's own slate and the IMDb primary genre via a coarse priority table: 57% of labelled hours have a group different from the first-listed genre's group.
- L3. Seven half-years only; the bootstrap describes dependence on titles, not viewer sampling; the permutation null (exchangeable positions) is imperfect when trends exist.
- L4. The "new" stratum includes titles that first crossed the report's listing threshold, not only new releases; hours have coarse resolution with many ties. Check 3 strata for H2 2023 use title-only comparison with H1 2023.
- L5. 3,836 keys have an unknown type (H1 2023-only titles); they are matched with the open type rule. Unlabelled (3 to 4.5% of in-scope hours) and out-of-scope hours (11.5 to 17.0% of listed hours) are excluded, never imputed; coverage by language tag differs slightly (tagged lower).
- L6. The bootstrap resamples labelled keys only (conditional on the labelling) and holds top-10 sets and new/carried flags at their observed values, as planned.
- L7. Right-censoring: no H2 2026 prediction is needed because nothing passes.

## Suggestions for the human (not run; outside the plan)
- The all-check permutation p of 0.039 with a negative observed M is easy to misread; consider whether the plan's p-value wording should require a pass first.
- Per-half scope instead of the union scope, and a different priority order in the mapping, were not tested; the 57% "group differs from first genre" figure suggests label sensitivity is the largest uncontrolled choice.
