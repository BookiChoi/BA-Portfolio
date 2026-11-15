Author: ai/validator
Overall verdict: PASS

# 06 Validation: Q1-Q4 (nyc-congestion-pricing)

Scope: every number in `05_analysis.md` was recomputed by an independent route, and the plan was checked against what was run. Result: 775 individual checks, 0 mismatches beyond tolerance. No number needed to be sent back. The items in section 5 are flags for the human, not failed numbers.

## 1. How it was checked (independent route)

| Item | Analyst | Validator |
|---|---|---|
| Aggregation | pyarrow per-file tables in `outputs/cache/` | DuckDB SQL straight on the 60 parquet files (`workflow/logs/validation_aggregate.py`, log `validation_aggregate.log`). Own validity rule from `taxi_zone_lookup.csv`, own CRZ list from the MTA csv. |
| Statistics | `pipeline/analyze.py`, `run_q1..q4.py` | `workflow/logs/validation_recompute.py` (log `validation_recompute.log`, all 775 rows in `validation_checks.csv`). Own bootstrap code, seeds 1001-1005 (analyst 42-47), Holm, Welch and Hedges g, statsmodels formula API (analyst: matrix API) for HC3 regression, Mann-Whitney as a non-parametric cross-check, geopandas union-intersects for neighbours. |
| Extra sensitivity | none | `validation_dedup.py` (duplicates), `validation_zoneid.py` (IDs outside lookup), out-of-sample top-5 selection, leave-one-month-out for Q4. |
| Tests | `tests/test_analyze.py` | `tests/test_validation_recompute.py` (3 passed, `pytest -q tests/test_validation_recompute.py`). |

Tolerances: counts and point estimates exact (1e-9 or 1e-7 for floats). Bootstrap CIs are compared with a different seed, so they are allowed to move: 1 zone for n50/n80 CIs (integer statistic), 0.15 pp for Q1 top-5 and Q2/Q4 CIs, 0.8 pp for Q3 monthly margin CIs (3-5 days per cell), 0.2-0.3 pp for fee shares. The largest observed CI deviation was 0.61 of its tolerance (Q3 HVFHV Feb 2026 margin CI low: analyst 1.97, validator 1.48 pp), apart from two integer CI ends that differ by exactly 1 zone (yellow morning n80 high 43 vs 42, HVFHV overnight n50 high 49 vs 48), which is the allowed discreteness.

## 2. Data checks (done first)

Commands: `validation_aggregate.py` then `validation_recompute.py` (sections "DATA CHECKS"), `validation_zoneid.py`, `validation_dedup.py`.

| Check | Result |
|---|---|
| Row counts vs `data_manifest.json` | 60 of 60 files match exactly. |
| Row counts vs analyst `file_quality_counts.csv` (total, null pickup, in-month, null IDs, invalid PU, invalid DO) | all 60 files identical. |
| Totals | yellow 104,587,416; HVFHV 604,313,696 rows (match 05). |
| Monthly row-count spread | yellow 2.82M-4.43M, max deviation from median 26%; HVFHV 17.96M-22.13M, max 10.6%. No month over the 30% flag line. |
| Missing values | 0 null pickup times, 0 null PU, 0 null DO in all 60 files. |
| Out-of-month pickups | yellow 1,113 rows (0.001%); HVFHV 0. |
| Invalid IDs (264/265) | yellow PU 0.48%, DO 0.94%; HVFHV PU 0.005%, DO 4.27% (all 60 files; exact counts in table below). Share of IDs outside the lookup: 0 in every service-year (the 0.1% stop rule is not triggered). |
| Joins and filters | There is no join. The only filters are in-month and valid ID, and each one is counted (see exclusion rows below). The valid-ID filter changes rows by design. |
| Duplicates | The plan keeps duplicates. Validator measured it: rows with the same (pickup, dropoff, PU, DO) are 1.14% of yellow rows (0.83% in 2023, 1.25% in 2024, 1.28% in 2026) and 0.0003% of HVFHV. In three sample yellow months, none of them are full-row duplicates (0 of 27,732 / 42,873 / 12,783 key duplicates), so they look like distinct trips. See flag F1. |

| Number | Analyst | Validator | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Rows vs manifest (60 files) | 60 match | 60 match | DuckDB count | 0 | PASS | |
| Analyst file_quality_counts vs DuckDB (60 files x 7 fields) | 0 differences | 0 differences | SQL vs pyarrow | 0 | PASS | |
| Yellow total trips (30 files) | 104,587,416 | 104,587,416 | DuckDB | 0 | PASS | |
| HVFHV total trips (30 files) | 604,313,696 | 604,313,696 | DuckDB | 0 | PASS | |
| Yellow invalid-PU / invalid-DO trips | 502,214 / 980,546 | 502,214 / 980,546 | DuckDB | 0 | PASS | |
| HVFHV invalid-PU / invalid-DO trips | 28,319 / 25,822,247 | 28,319 / 25,822,247 | DuckDB | 0 | PASS | |

## 3. Plan conformance (`04_analysis_plan.md`)

| Plan item | Status |
|---|---|
| Step 1 schema check, 60 files, manifest entries | Done. Manifest has 63 entries (60 parquet, lookup, CRZ list, `.shp`). Row counts verified above. |
| Step 2 lookup, airports, CRZ list (38 IDs), neighbours (open item B) | Done. Neighbour set recomputed: 43, 140, 141, 142, 143, 237 (identical). |
| Q1 day-parts, n50/n80, top-5, hypotheses (a) and (b), guidance lists 50%/40%, standing/seasonal, Jaccard | Done and recomputed. |
| Q1 chart 3 (heat table "per service for whole-day or each day-part") | Whole-day heat tables only (`q1_standing_seasonal_{yellow,fhvhv}.png`). Day-part lists are in CSV. Minor. |
| Q2 shares, top-5 with re-selection, Holm over 6, pairs under 1,000 trips undecided | Done. |
| Q3 day-level night share, Welch, Hedges g, Holm over 24, pooled HC3, S1, S2, S3 | Done. |
| Q3 bootstrap "within month and day type" | Deviation (disclosed by analyst in 05): resamples inside month x day-of-week cells because `spread_m` needs the cells. Validator used the same cells and got CIs within tolerance. Not a number failure. See F4. |
| Q3 S3 reading | The plan's S3 text is contradictory (literal assignment vs stated intent). The analyst ran both readings, labelled them, and left the choice open. Reported as found, not resolved (see F2). The "intent" reading is an addition beyond the literal plan text. |
| Q4 shares, drift, bootstrap, Holm over 2, S4, fee check, edge-zone flag, supplementary and neighbour tables | Done. |
| Analysis run but not in plan | Q3 pooled regressions for S1-S3 and the second S3 reading ("intent"). No other additions found. |
| Planned but missing | None found. |

## 4. Recomputed numbers

All rows below: PASS. "Method" gives the independent route. The full list of 775 checks (including every monthly Q3 value, all 30 monthly Q4 shares per service and year, every day-part value) is in `workflow/logs/validation_checks.csv`.

### Q1

| Number | Analyst | Validator | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Yellow valid trips | 46,415,189 | 46,415,189 | DuckDB sum | 0 | PASS | |
| HVFHV valid trips | 253,396,936 | 253,396,936 | DuckDB sum | 0 | PASS | |
| Yellow excluded invalid PU | 79,145 | 79,145 | DuckDB | 0 | PASS | |
| HVFHV excluded invalid PU | 12,835 | 12,835 | DuckDB | 0 | PASS | |
| Yellow n50 / n80 | 17 / 36 | 17 / 36 | sorted cumsum | 0 | PASS | |
| HVFHV n50 / n80 | 60 / 128 | 60 / 128 | sorted cumsum | 0 | PASS | |
| Yellow top-5 share | 19.64% | 19.638% | sorted cumsum | 1e-9 | PASS | CI [19.46, 19.84] vs own [19.47, 19.83] |
| HVFHV top-5 share | 7.17% | 7.169% | sorted cumsum | 1e-9 | PASS | |
| Active zone share yellow / HVFHV | 98.86% / 99.24% | same | count>0 / 263 | 1e-9 | PASS | |
| n80 CIs (both services, 6 day-part rows each) | in 05 | same within 1 zone | own week bootstrap, B=2000, seed 1001 | 1 zone | PASS | |
| Day-part n80 yellow (39, 41, 33, 34, 32) | as 05 | same | sorted cumsum | 0 | PASS | |
| Day-part n80 HVFHV (115, 136, 133, 126, 115) | as 05 | same | sorted cumsum | 0 | PASS | |
| H(b) d = n80(HVFHV) - n80(yellow) | 92 [91, 93] | 92, CI within 1 zone | paired week bootstrap | 1 zone | PASS | |
| H(b) ratio | 3.556 | 3.556 | recomputed | 1e-9 | PASS | |
| H(b) one-sided p | 0.0005 | 0.0005 | bootstrap +1 rule | 0.0005 | PASS | both at the floor 1/2001 |
| Day-part d (75-100 zones) | as json | same | recomputed | 0 | PASS | |
| Airport ranks yellow: JFK 3, LGA 14, EWR 181 | as 05 | same | lexsort | 0 | PASS | months in monthly top 5: 12, 0, 0 |
| Airport ranks HVFHV: LGA 1, JFK 2, EWR 261 | as 05 | same | lexsort | 0 | PASS | months in top 5: 12, 12, 0 |
| Guidance list sizes (all hours): yellow 17 (50%), HVFHV 43 (40%) | 17 / 43 | 17 / 43 | recomputed cover list | 0 | PASS | membership identical as sets |
| Standing zones: yellow 15, HVFHV 38 | as 05 | same | recomputed | 0 | PASS | |
| Jaccard all hours: yellow 0.889-1.000 (mean 0.963), HVFHV 0.889-0.977 (mean 0.940) | as 05 | same | recomputed | 1e-9 | PASS | all 12 service x day-part lists also match (60 rows in csv) |

### Q2

| Number | Analyst | Validator | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Counts: all pickups, valid dest, excluded, same-airport (6 pairs) | as 05 table | same | DuckDB | 0 | PASS | e.g. HVFHV JFK 3,220,341 valid, 813,005 excluded |
| Yellow Newark top5 / delta | 98.23% / +78.59 pp | 98.232% / +78.594 | sorted cumsum | 1e-7 | PASS | CI [78.18, 79.11] vs own [78.16, 79.14] |
| Yellow JFK top5 / delta | 16.22% / -3.42 pp | same | same | 1e-7 | PASS | CI own [-3.73, -3.13] |
| Yellow LGA top5 / delta | 18.58% / -1.06 pp | same | same | 1e-7 | PASS | CI own [-1.76, -0.43] |
| HVFHV JFK top5 / delta | 11.71% / +4.54 pp | same | same | 1e-7 | PASS | CI own [4.25, 4.82] |
| HVFHV LGA top5 / delta | 15.72% / +8.55 pp | same | same | 1e-7 | PASS | CI own [7.94, 9.07] |
| HVFHV Newark | 11 valid trips, no decision | same | rule: under 1,000 | n/a | PASS | |
| Ratios (5 pairs) | 5.00, 0.83, 0.95, 1.63, 2.19 | same | recomputed | 1e-9 | PASS | |
| Decisions (rule on point estimate) | as 05 | same | recomputed | exact | PASS | |
| Holm p (family 6, blank counted as 1) | 0.003, 1, 1, 0.003, 0.003 | same | own Holm | 0.0005 | PASS | |
| Top-5 destination ID lists (5 pairs) | as csv | same | ranking recomputed | exact | PASS | |

### Q3

| Number | Analyst | Validator | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Days 365; weekday 250; weekend 104; holidays 11 (both services) | as 05 | same | recount from DuckDB | 0 | PASS | holiday list equals the plan table |
| Trips used (yellow / HVFHV) | 46,494,334 / 253,409,771 | same | DuckDB | 0 | PASS | |
| Yellow gap_m range | 10.08-16.02 pp | same | pooled night / total | 1e-7 | PASS | min Dec 2025, max Mar 2026 |
| Yellow spread_m range | 2.78-5.81 pp | same | recomputed | 1e-7 | PASS | |
| HVFHV gap_m range | 9.12-11.10 pp | same | recomputed | 1e-7 | PASS | |
| HVFHV spread_m range | 1.08-2.72 pp | same | recomputed | 1e-7 | PASS | |
| Smallest margin yellow (Dec 2025) | 4.27 pp [1.78, 6.09] | 4.27 [1.82, 6.13] | own day bootstrap in DOW cells, seed 1003 | 0.8 pp | PASS | |
| Smallest margin HVFHV (Dec 2025) | 6.57 pp [3.42, 7.88] | 6.57 [3.58, 7.81] | same | 0.8 pp | PASS | |
| Weekday / weekend night share ranges | 13.0-15.9 / 25.6-29.3 (yellow); 16.2-18.5 / 26.3-28.5 (HVFHV) | same | recomputed | 1e-9 | PASS | |
| Months passing gap>0 and gap>spread | 12 / 12 both | 12 / 12 both | recount | 0 | PASS | decision: separate night guidance (both) |
| Welch t, Hedges g (24 months) | g 2.75-7.88 | g 2.75-7.88 | scipy ttest_ind(Welch), own formula | 1e-6 | PASS | |
| Largest Holm p over 24 | 0.00045 | 0.00045 | own Holm | 1e-6 | PASS | Mann-Whitney one-sided p < 0.05 in 24 of 24 months (agreement) |
| Pooled weekend effect yellow | 13.12 pp [12.36, 13.87] | 13.12 [12.36, 13.87] | statsmodels formula OLS, month FE, HC3 | 1e-6 | PASS | |
| Pooled weekend effect HVFHV | 10.16 pp [9.63, 10.69] | 10.16 [9.63, 10.69] | same | 1e-6 | PASS | |
| S1 months passing / pooled | 12/12; 12.87, 9.88 pp | same | recomputed | 1e-6 | PASS | |
| S2 months passing / pooled | 12/12; 13.06, 9.97 pp | same | recomputed | 1e-6 | PASS | |
| S3 literal: gap>spread months | yellow 4, HVFHV 9 | 4, 9 | own date re-assignment of hours 0-4 | 0 | PASS | pooled 4.57, 3.97 pp match |
| S3 intent: gap>spread months | yellow 12, HVFHV 11 | 12, 11 | own re-assignment | 0 | PASS | pooled 13.31, 9.65 pp match |
| Hourly profile spot checks (hours 3, 8, 18; both day types, both services) | in csv | same | pandas | 1e-6 relative | PASS | |

### Q4

| Number | Analyst | Validator | Method | Tolerance | Result | Notes |
|---|---|---|---|---|---|---|
| Yellow share 2023 / 2024 / 2026 | 73.83 / 73.65 / 71.67% | same | DuckDB flags | 1e-9 | PASS | in-zone and denominator counts also exact |
| HVFHV share 2023 / 2024 / 2026 | 36.43 / 34.74 / 30.48% | same | same | 1e-9 | PASS | |
| Excluded share yellow (2023, 2024, 2026) | 1.74, 1.05, 0.68% | same | DuckDB | 1e-9 | PASS | |
| Excluded share HVFHV | 4.07, 4.12, 4.50% | same | DuckDB | 1e-9 | PASS | |
| Yellow Delta_main / Delta_drift | -1.99 / -0.18 pp | same | recomputed | 1e-7 | PASS | CI own [-2.76, -1.23] / [-0.69, 0.30] |
| HVFHV Delta_main / Delta_drift | -4.26 / -1.69 pp | same | recomputed | 1e-7 | PASS | |
| Yellow margin abs(main) - abs(drift) | +1.81 pp [0.74, 2.60] | +1.81 [own 0.75, 2.64] | own week bootstrap seed 1004 | 0.15 pp | PASS | |
| HVFHV margin | +2.57 pp [1.73, 3.46] | +2.57 [own 1.65, 3.42] | same | 0.15 pp | PASS | |
| Relative change main | -2.70%, -12.26% | same | recomputed | 1e-9 | PASS | |
| Holm p (2 tests) | 0.001 both | 0.001 both | own Holm | 0.0005 | PASS | raw p at floor |
| Decision (point estimate) | real shift: review (both) | same | rule | exact | PASS | |
| S4 shares and margin | yellow 72.90/73.22/71.40, +1.50; HVFHV 36.41/34.71/30.69, +2.33 | same | recomputed | 1e-7 | PASS | |
| Monthly shares (54 values) | in csv and 05 text | same | DuckDB | 1e-9 | PASS | text ranges in 05 (69.3-70.6, 29.6-31.6, 33.7-35.4) match |
| Fee check yellow: fee>0 trips, (i), (ii) | 33,517,577; 95.98%; 97.07% | same | DuckDB | exact / 1e-9 | PASS | CIs within 0.3 pp |
| Fee check HVFHV: fee>0 trips, (i), (ii) | 82,792,577; 94.35%; 99.06% | same | same | exact / 1e-9 | PASS | |
| Zones: list zones with fee share < 50% | 0 (both) | 0 | recomputed | 0 | PASS | |
| Zones outside list with fee share > 50% | yellow 9, HVFHV 7 | 9, 7 | recomputed | 0 | PASS | IDs: yellow 43,66,105,138,141,142,143,199,237; HVFHV 43,105,140,141,142,143,237 |
| Neighbour zone set | 43,140,141,142,143,237 | same | geopandas union.intersects | exact | PASS | |
| Neighbour combined share change (pickup/dropoff) | yellow -0.71/-0.75 pp, HVFHV -0.30/-0.24 pp | same | recomputed | 1e-7 | PASS | |
| 38-zone combined pickup share change | -2.53 / -2.98 pp | -2.530 / -2.977 | recomputed | 0.006 | PASS | |
| Top-15 gain zone sets (4 service x kind) | as csv | same | recomputed | exact | PASS | |

## 5. Assumptions, sensitivity and flags (for the human; none is a failed number)

Statistical assumptions checked:
- Sample size: very large; p-values are at their floor (0.0005, B = 2000), so the effect sizes and CIs carry the information, as the plan says. The Q2 HVFHV Newark pair (11 valid trips) is correctly left without a decision.
- Selection effect (Q2): the top 5 is chosen on the data it is measured on. Validator test: choose the top 5 on odd weeks and measure on even weeks. Result: airport vs overall top-5 shares, no decision changes (yellow Newark 97.7% vs 19.7%, JFK 16.3% vs 19.7%, LGA 18.4% vs 19.7%; HVFHV JFK 11.7% vs 7.2%, LGA 15.7% vs 7.2%). The upward bias is small (about 0.1-0.3 pp).
- Leakage: none found; no model is fitted and no outcome variable is reused as a predictor.
- Outliers and trimming: none applied (counts only), as planned. Out-of-month rows are 0.001% (yellow).
- Q3 variance and independence: day-level shares are not independent (weekly rhythm); the analyst states this. Non-parametric Mann-Whitney agrees in 24 of 24 month-service tests, so the result does not rest on normality.
- Multiple comparisons: Holm per question as planned; recomputed Holm values match.
- Q4 stability: leave-one-month-out (drop one of Jan-Sep from all three years) keeps the rule at "real shift": yellow margin +1.47 to +2.13 pp, HVFHV +2.40 to +2.70 pp.

Flags:
- F1, duplicates (yellow). 1.14% of yellow rows share pickup, dropoff, PU and DO with another row (none are full-row duplicates in sampled months). The plan keeps duplicates. Validator sensitivity (`validation_dedup.log`): removing them moves yellow Q4 shares by under 0.1 pp (2023 73.83 to 73.92%, 2024 73.65 to 73.75%, 2026 71.67 to 71.70%) and the margin from +1.81 to +1.89 pp. HVFHV is unchanged. The decision does not change.
- F2, Q3 S3 wording (literal vs intent): found as the analyst described. The two readings give different yellow results (literal: gap > spread in 4 of 12 months; intent: 12 of 12) and HVFHV (9 and 11 of 12). Validator reproduces both sets exactly. Not resolved here; it needs the human's reading of 02.
- F3, Q4 yellow timing. The yellow drop is concentrated in Jan-May (2026 vs 2024: -3.19 pp; drift -0.09 pp). For Jun-Sep, 2026 vs 2024 is -0.40 pp and drift is -0.34 pp, so the margin there is about zero. The all-months decision "real shift" is right under the rule, but the pattern is uneven. HVFHV falls in both periods (-4.53 and -3.91 pp), and its drift is already -1.69 pp (the baseline is not flat). The drift baseline is a single year pair (03 and 05 both say so).
- F4, Q3 bootstrap unit differs from the plan text (DOW cells). Disclosed in 05; the validator reproduced CIs with the same unit within tolerance, but did not test a day-type-only bootstrap.
- F5, yellow Newark (Q2). The rule passes because 97.7% of 6,109 valid trips go to Newark Airport itself. The number is correct; the interpretation is the human's.
- F6, HVFHV destinations: about 20% of JFK and 13% of LGA pickups end at IDs 264/265 and are excluded from Q2 shares (numbers verified: 813,005 and 659,634).
- F7, files left by the validator: `workflow/logs/validation_cache/agg.pkl` (about 315 MB, regenerable with `validation_aggregate.py`) and the small `q2_oos.pkl`. The validator has no delete permission. Do not commit them. `outputs/cache/` of the analyst is also not covered by `.gitignore` (05 says so).
- Not verified: that naive timestamps are New York local time (not testable from the files); that taxi zone IDs keep the same meaning across 2023-2026; the PNG charts (only the data behind them).

## 6. Files written by the validator

- `workflow/06_validation.md` (this file)
- `workflow/logs/validation_aggregate.py` and `.log`, `validation_recompute.py` and `.log`, `validation_checks.csv`, `validation_dedup.py` and `.log`, `validation_zoneid.py` and `.log`, `validation_summary.py`
- `tests/test_validation_recompute.py`
