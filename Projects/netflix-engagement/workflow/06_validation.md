Author: ai/validator
Overall verdict: PASS

# 06 Validation: Netflix engagement, Q1 (as-of 2026-11-12)

Scope: every number in `05_analysis.md` that the committed outputs allow me to recompute. No number failed. Two parts of the chain were re-run with the analyst's own code, so they are not independent (see "Limits of independence"). Nothing in the analyst's code or outputs was modified; I wrote only the files listed at the end.

## 1. Data checks (done first)
Own reader (openpyxl only, not `pipeline.load`). Log: `workflow/logs/validation_quick.log`, test `tests/test_validation_data.py`, `tests/test_validation_dups.py`.

| Check | Result |
|---|---|
| Row count per file vs `data_manifest.json` | All seven files match exactly (18,214 / 15,994 / 16,161 / 15,563 / 16,182 / 16,470 / 17,372). Total 115,956 = `clean_log.json` `rows_in`. |
| Missing or non-numeric hours | 0. Zero or negative hours: 0. |
| Full-row duplicates (all columns) | 0, same as `clean_log.json`. |
| Same title more than once in a file | 1 to 5 per file from 2024 H1 on. All have different release dates and runtimes, so they are different works (for example Monster 2024 vs Monster 2021, Maria 2024 vs 2019, War Machine 2026 vs 2017). The key merge (P2) sums them into one key and gives them one IMDb match. This is a planned rule, but the hours are small (the 2017 War Machine row has 0.9M hours). See note N3. |
| Row changes from joins and filters | Cleaning merges 20,611 rows into 9,111 keys (as `clean_log.json`). The scope union is 4,398 keys; my own scope routine returns the identical set (symmetric difference 0). Matrix hours reproduce the analyst's `variant_hours.csv` exactly (difference 0.0). |
| Hours totals per half | My raw sums equal `all_listed_hours` in `coverage_by_half.csv` to the hour, all seven halves. |
| Missing release dates | Not used for any reported number; not checked beyond the profile. |

## 2. Plan conformance
- Run and in the plan: P1 to P5, pilot gate, checks 1 to 3, cluster bootstrap (2,000), exact permutation tests (5,040 and 720), Newcombe CIs, pair rule (not triggered), theta sensitivity at 1.5 and 3, post-stratification, charts 1 to 5.
- Chart 6 correctly not produced (no pass).
- Run but not in the plan: the "group differs from first genre" figure (54.3% of keys, 57.0% of hours). It was requested by the human in the pilot decision, so it is conformant. Not recomputed by me (needs the analyst's genre-first logic); I did verify the priority-table mapping itself (below).
- Planned but only partly done: the plan asks for proportion differences with Newcombe CIs by tagged/untagged. The analyst applied Newcombe to key counts and gave hours-weighted coverage as point values only; this is disclosed in `05_analysis.md`. Not a numeric error.
- The plan states the gate file as `workflow/05_pilot_check.md`; the file is `workflow/05_pilot_check` (no extension). The code accepts both. Cosmetic.
- Scope rule where the plan was silent (union keys counted in every half where present) was disclosed by the analyst; I reproduced it.

## 3. Recomputation table
Tolerance for deterministic numbers: 1e-6 pp (floating point). For bootstrap interval endpoints: 0.5 pp (2,000 replicates, different seed and a different resampling routine: integer index draws instead of multinomial counts).

| Number | Analyst value | My value | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Rows total, 7 files | 115,956 | 115,956 | openpyxl own reader | exact | PASS | per-file counts also exact |
| Listed hours per half (7 values) | e.g. H1 2023 93,455,200,000 | identical for all 7 | own sum of raw hours | 1 hour | PASS | includes the 4 "Other" rows |
| Scope union keys | 4,398 | 4,398 | own cumulative-share routine, 80% target | exact | PASS | symmetric difference 0 |
| Genre mapping of 4,398 keys | priority table | 0 mismatches | re-implemented priority rule from `genre_mapping.csv` | 0 | PASS | all distinct IMDb genres are in the mapping |
| Shares, 4 variants x 8 genres x 7 halves | `shares_all_variants.csv` | max abs diff 3.6e-15 pp | own hours matrix, own top-10 and new/carried masks, pandas/numpy loops | 1e-6 | PASS | uses the analyst's labels (see limits) |
| Shares sum to 100 per variant and half | 100 | 100 (+/- 1e-14) | sum | 1e-6 | PASS | NaN only for c3 strata in H1 2023 |
| Unlabelled / in-scope hours, 7 halves | 3.08 to 4.49% | identical to 3 decimals | own matrix | 0.01 pp | PASS | max 4.494% in H1 2026, below the 10% rule |
| Top-10 cells in unlabelled keys | 1 | 1 | own top-10 | exact | PASS | |
| Eligible genres (mean share >= 5%) | 7 genres | same 7 | mean of 7 shares | exact | PASS | Drama is 4.88% (see N2) |
| Mean shares (8 genres) | e.g. Crime & Thriller 30.94 | same, 2 decimals | mean of c1 shares | 0.005 | PASS | |
| Six check-1 shifts x 7 genres | `shift_1..6` | max diff 3.6e-15 | difference of shares | 1e-6 | PASS | |
| Margins c1, c2, c3 new, c3 carried x 7 genres | table in section Q1 | max diff 3.6e-15 | own loop; direction sign set by position, c3 uses d2..d6 | 1e-6 | PASS | 28 numbers |
| Genre margin and direction x 7 | e.g. Sci-Fi -0.54 up | same | max over direction of min over 4 checks | 1e-6 | PASS | |
| Mean aligned shift (check 1) x 7 | e.g. Sci-Fi 1.85 | same | mean of six aligned shifts | 1e-6 | PASS | |
| Mean aligned shift c3 new/carried, 5 transitions x 7 | in `genre_results.csv` | same | mean of d2..d6 | 1e-6 | PASS | |
| Passing genres at 1.5, 2, 3 pp | 0, 0, 0 | 0, 0, 0 | threshold test on my margins | exact | PASS | no near miss within 0.05 pp (best genre margin -0.54) |
| Permutation, check 1: M, p, any-pass counts | M +0.49, p 0.138, 24/0/0 | +0.4852, 0.1381, 24/0/0 | independent enumeration of 5,040 orderings (own loops) | 1e-9 on p, exact counts | PASS | |
| Permutation, all checks: M, p, any-pass counts | M -0.54, p 0.039, 0/0/0 | -0.5358, 0.0389, 0/0/0 | independent enumeration of 720 orderings | same | PASS | |
| Single-genre reference | 3.125% | 3.125% | 2 x 0.5^6 | exact | PASS | |
| Match rate tagged / untagged / all with Wilson CI | 93.58, 94.59, 94.27 | agree for all 6 rows | scipy `binomtest` Wilson | 0.01 pp | PASS | counts x, n taken from the analyst's CSV |
| Newcombe CI, matched and labelled | -1.02 [-2.61, 0.44]; -0.99 [-2.58, 0.47] | same to 3 decimals | own implementation of method 10 | 1e-6 | PASS | |
| Newcombe CI per half, 7 halves | -4.1 [-6.7, -2.0] ... -0.9 [-2.5, 0.5] | same | own implementation | 0.002 | PASS | key counts reconstructed from rounded rates |
| Post-stratified check-1 margins x 7 genres, up and down | e.g. Kids & Family +0.13, Sci-Fi +0.50 | max diff 1.2e-14 | own reweighting (in-scope hours / labelled hours per language group) | 1e-6 | PASS | |
| Bootstrap: mean aligned shift CI x 7 | e.g. Sci-Fi [0.33, 3.46] | [0.35, 3.46] | 2,000 resamples, seed 20261112, integer-index draws | 0.5 pp | PASS | worst endpoint diff 0.08 |
| Bootstrap: check-1 margin CI x 7 | e.g. Crime [-7.45, -1.13] | [-7.34, -1.10] | same | 0.5 pp | PASS | worst endpoint diff 0.15 |
| Bootstrap: check-2 margin CI x 7 | e.g. Crime [-5.01, 0.34] | [-5.01, 0.19] | same | 0.5 pp | PASS | worst endpoint diff 0.15 |
| Bootstrap: genre margin CI x 7 | e.g. Crime [-12.88, -2.50] | [-12.69, -2.47] | same, direction re-chosen per replicate (the plan's definition), seed 777 | 0.5 pp | PASS | worst endpoint diff 0.44. With the direction fixed at the observed one, endpoints differ by up to 4 pp, which is a definition difference, not an error |
| Bootstrap pass fraction at 1.5 and 2 pp x 7 | 0.000 | 0.000 | same | 0.01 | PASS | |
| Analyst point estimates inside my bootstrap intervals | n/a | 28 of 28 | comparison | n/a | PASS | |
| Largest single shifts (Sci-Fi +4.86, -3.60) | +4.86, -3.60 | +4.858, -3.598 | share differences | 0.01 | PASS | |

Not recomputed independently: bootstrap CIs for check 3 new/carried margins (they enter the genre-margin CI, which I did recompute); the 3,836 unknown-type key count; the 725 ambiguous-key count and tie-break counts (these come from the matching code, which I re-ran but did not re-derive); Wilson/Newcombe values for labelled-rate-by-half beyond the rounding of the CSV.

## 4. Statistical assumptions and sensitivity
- Sample size: seven half-year points per genre and six transitions. A pass on four checks at 2 pp is a demanding rule; the exact enumeration shows no ordering of the seven shares passes at 2 pp (0 of 5,040), so a pass would have been rare even by chance. Result agrees.
- Multiple comparisons: the max-statistic permutation test is the right family-wise device and I reproduced it exactly. The all-checks p of 0.039 comes with a negative observed M (-0.54 pp), so it does not indicate a pass; the analyst states this correctly in `05_analysis.md`.
- Leakage: none (no prediction was made; chart 6 absent).
- Selection and survivorship: scope is the union of titles in the top 80% of any half, and the "new" stratum includes titles that first crossed the listing threshold. Analyst discloses both (L4). The new stratum is only about a quarter of carried hours, and its CIs are wide (a width of 10 to 20 pp for the margin).
- Outlier sensitivity: the one big swing is Sci-Fi & Fantasy H1 2025 to H2 2025 (+4.86 pp), driven by Stranger Things (0.40e9 to 2.49e9 hours) and Wednesday (0.09e9 to 1.28e9). Check 2 (top-10 dropped) removes this; the Sci-Fi check-2 margin is -0.54 pp. My extra test dropping the top 25 labelled keys per half left no genre near 2 pp (best margins all below 0.21 pp for either direction on check 1, log `workflow/logs/validation_rebuild.log`).
- Label sensitivity (largest uncontrolled choice, as the analyst says): see N1 and N2.

## 5. Notes for the human (no action required for the verdict)
- N1. Label spot check. For a random 400 keys I matched title to IMDb by a simpler route (exact normalised primary title, type filter, most votes, no year filter, stage 1 only). Of 358 comparable labelled keys, 351 gave the same group (98.0%); 7 differed (The Killer, Life, The Wages of Fear, The Circle, The Gift, The Hunt, Jack). All are common titles where the analyst's year filter or segment rule could legitimately choose another work, so I cannot call them errors. This is a spot check on generic titles, not a replacement for the human hand check of the ambiguous keys (L1).
- N2. Drama has mean share 4.88%, just under the 5% eligibility line. If it were eligible, its best genre margin would be -1.40 pp (both directions fail check 1), so the result would not change. The eligibility rule is as planned.
- N3. Same-title different-work rows (Monster, Maria, War Machine, "You vs. Wild: Season 1" with two release dates) are merged into one key by the planned P2 rule. The hours involved are small, but the merged key takes the genre of one work.
- N4. The Drama and top-25 checks above use my own routes and are not analyst numbers; they are extra sensitivity information only and are not part of the verdict.

## Limits of independence
- Cleaning and key building (`pipeline/clean.py`) and IMDb matching (`pipeline/label.py`) were called as the analyst wrote them to obtain keys and labels. Everything from the hours matrix onward (scope check, top-10, new/carried, shares, margins, permutation, bootstrap, post-stratification, Newcombe, group mapping) is my own code. The raw hours were read with my own reader. A bug in key cleaning or matching would not be caught except through the 98.0% spot check.
- `workflow/05_pilot_check` was not re-verified; the analyst already flags it as an AI-only check.

## Files I wrote
- `workflow/06_validation.md` (this file)
- `tests/test_validation_data.py`, `tests/test_validation_dups.py`, `tests/test_validation_shares.py`, `tests/test_validation_rebuild.py`, `tests/test_validation_boot2.py`, `tests/test_validation_poststrat.py` (all pass; rebuild/boot2/poststrat need the raw files in `~/Downloads` and take about 70 seconds each)
- `workflow/logs/validation_quick.log`, `workflow/logs/validation_rebuild.log`, `workflow/logs/validation_boot2.log`, `workflow/logs/validation_poststrat.log`

Commands: from the project folder, `../../.venv/bin/python -m pytest -q -s tests/test_validation_<name>.py -p no:cacheprovider`.
