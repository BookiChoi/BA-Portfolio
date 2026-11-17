Author: ai/analyst

# 05 Analysis: Q1-Q4 (Phase B)

Executed the plan in `04_analysis_plan.md` (approval line present, at the end of the file, after the human's Gate 2 block). No insights or recommendations here; those are the human's.

Run everything: `MPLBACKEND=Agg python main.py all` (from the project folder; `FORCE_AGG=1` rebuilds the per-file aggregates). Each stage writes its printed output to `outputs/logs/<stage>.log`. That log is the evidence for every number below. Tests: `pytest -q` (6 passed).

## 0. Setup and evidence index

- Seed: 42 (`pipeline/config.py`). Streams: Q1 seed 42; Q2 seed 44; Q3 seed 45 (re-seeded per monthly call); Q4 seed 46 (fee check seed 47). Every bootstrap B = 2000, 95% percentile CI, calendar-week (Mon-Sun) blocks. Reason for separate streams: each question is reproducible alone.
- Libraries: pyarrow 26.0.1, pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.10.9, geopandas 1.2.0 (shapely, pyogrio, pyproj versions as installed by the human; not re-queried).
- Code: `pipeline/config.py`, `load.py`, `aggregate.py`, `analyze.py`, `visualize.py`, `run_step1.py`, `run_step2.py`, `run_aggregate.py`, `run_q1.py` .. `run_q4.py`; `main.py`; `tests/test_analyze.py`.
- Intermediate per-file count tables: `outputs/cache/` (about 27 MB, regenerable). Do not commit; it is not covered by `.gitignore`. Raw data was never exported.
- Reduction of months: none needed. All 60 files processed (about 0.5-5 s per file with column pruning).

## 1. Step 1: schema and file check (stage log `outputs/logs/step1.log`, script `pipeline/run_step1.py`)

Result: PASS for both services; no stop condition triggered.
- 30 files per service, none with zero rows. Required fields present in all 60 files: pickup datetime, dropoff datetime, `PULocationID`, `DOLocationID`. `cbd_congestion_fee` (double) present in all 12 Oct 2025 - Sep 2026 files per service, absent in all 2023-2024 files (expected).
- Dtypes: pickup/dropoff `timestamp[us]` with no timezone (naive) in all files. Assumption carried (not verifiable from schema): naive = New York local wall clock. Location IDs int32, except int64 in the two 2023-01 files (integer-like, accepted).
- Other schema differences (flag, no stop): yellow `Airport_fee` casing and the 2026-06..09 files add `request_source`; yellow 2023-01 has `airport_fee` and different types; HVFHV 2025-10 onward adds `cbd_congestion_fee`. 7 distinct column-set signatures in total (listed in the log).
- Row counts: yellow 2.82M-4.43M per month, HVFHV 17.96M-22.13M. No month deviates more than 30% from its service median. Flag: yellow Oct-Dec 2025 (4.18M-4.43M) is above the human's sample range (3.0-3.7M), and HVFHV 2023-02 (17.96M) is below the sample range (about 19.7M).
- `data_manifest.json`: 63 entries (60 Parquet, lookup, CRZ list, shapefile `.shp`) with source URL, download date 2026-11-13, row count, sha256, licence note "no explicit licence on TLC page; terms not found, checked 2026-11-13". Shapefile sidecar files (.dbf .shx .prj .cpg) and `taxi_zones.zip` are not listed separately.

## 2. Step 2: lookup, zone lists (log `outputs/logs/step2.log`, script `pipeline/run_step2.py`)

- Lookup has 265 distinct IDs. Invalid IDs = 264 (Unknown) and 265 (Outside of NYC): 263 valid zones. Null IDs would also be invalid (none found).
- Airports 1 Newark Airport, 132 JFK Airport, 138 LaGuardia Airport match the lookup.
- CRZ list: `data/MTA_Central_Business_District_Taxi_Zones_20261113.csv`, column "Taxi Zone": 38 distinct IDs, all in the lookup, none 264/265, all Manhattan. Names printed in the log. Saved as `outputs/reference/crz_zone_ids.csv` before results. Airport list: `outputs/reference/airport_zone_ids.csv`. Holiday list: `outputs/reference/holidays_excluded_weekdays.csv` (11 dates, as in plan Q3). Invalid IDs: `outputs/reference/invalid_zone_ids.json`.
- Neighbouring zones by geometry (open item B): shapefile 263 rows, EPSG:2263, 263 distinct IDs, all 38 CRZ IDs present. Rule as given: not in the list and `intersects` at least one CRZ zone, no tolerance. Result: 6 zones: 43 Central Park, 140 Lenox Hill East, 141 Lenox Hill West, 142 Lincoln Square East, 143 Lincoln Square West, 237 Upper East Side South (`outputs/reference/crz_neighbour_zone_ids.csv`). Observation for the human: no zone across the rivers (Brooklyn, Queens, New Jersey, islands) touches the list under the no-tolerance rule. Not changed.
- Per-file quality counts (total rows, null/out-of-month pickups, in-month rows, invalid PU/DO): `outputs/reference/file_quality_counts.csv` (log `outputs/logs/aggregate.log`). Across all 60 files: no null pickup times, no null IDs. Out-of-month rows are tiny (for example yellow 2023-03: 189 of 3,403,766). Invalid-DO trips are 25,822,247 of 604,313,696 HVFHV trips and 980,546 of 104,587,416 yellow trips; invalid-PU 28,319 HVFHV and 502,214 yellow (sums from the log).

## 3. Q1: pickup zones by part of the day, and concentration

Method: counts of valid-PU trips per zone and day-part (hours 0-5, 6-9, 10-15, 16-19, 20-23), Oct 2025 - Sep 2026; n50/n80, top-5 share, rank check, guidance lists with 50% coverage (40% if the list is longer than 30 zones), standing/seasonal flags, Jaccard; week-block bootstrap (53 weeks, services paired on the same weeks). Script `pipeline/run_q1.py`, log `outputs/logs/q1.log`.
Charts: `outputs/q1/q1_top10_by_daypart.png`, `q1_cumulative_share.png`, `q1_standing_seasonal_yellow.png`, `q1_standing_seasonal_fhvhv.png`. Aggregated data: `outputs/q1/q1_top10_by_daypart.csv`, `q1_cumulative_share.csv`, `q1_concentration.csv`, `q1_hypothesis_b.json`, `q1_airport_rank_check.csv`, `q1_guidance_lists.csv`, `q1_monthly_membership.csv`, `q1_monthly_jaccard.csv`, `q1_exclusions_by_month.csv`.

Exclusions (log q1): yellow 46,494,334 in-month trips, 79,145 excluded for invalid PU (0.1702%); HVFHV 253,409,771 trips, 12,835 excluded (0.0051%). Month detail: `q1_exclusions_by_month.csv`.

Results, all hours, with 95% CI (`q1_concentration.csv`):

| Service | Valid trips | n50 | n80 | Top-5 pickup share | Zones with any trip |
|---|---|---|---|---|---|
| Yellow | 46,415,189 | 17 [17, 17] | 36 [36, 36] | 19.64% [19.46, 19.84] | 98.86% |
| HVFHV | 253,396,936 | 60 [59, 60] | 128 [127, 129] | 7.17% [7.08, 7.27] | 99.24% |

Day-part n80 (yellow / HVFHV): overnight 39 / 115, morning 41 / 136, midday 33 / 133, evening 34 / 126, night 32 / 115. n50 by day-part is in the CSV.

Hypothesis (b), n80(HVFHV) > n80(yellow): d = 92 zones [91, 93], ratio 3.56 [3.53, 3.58], one-sided bootstrap p = 0.0005 (the smallest value with B = 2000). Single confirmatory test, no correction. Day-part differences are descriptive (75-100 zones, `q1_hypothesis_b.json`).

Hypothesis (a), airports in the top 5 for the whole period (`q1_airport_rank_check.csv`):
- Yellow: JFK rank 3 (top 5 in 12 of 12 months); LaGuardia rank 14 (0 of 12 months); Newark rank 181 (0 of 12; 6,333 trips).
- HVFHV: LaGuardia rank 1 and JFK rank 2 (12 of 12 months each); Newark rank 261 (17 trips).
- So the hypothesis holds for HVFHV (JFK, LaGuardia) and for yellow JFK only.
- Yellow top 5: Upper East Side South, Midtown Center, JFK, Upper East Side North, Penn Station/Madison Sq West. HVFHV top 5: LaGuardia, JFK, Crown Heights North, East New York, Times Sq/Theatre District.

Guidance lists (all hours): yellow 17 zones at 50% coverage (15 standing, 2 seasonal: Clinton East 11/12 months, Lenox Hill West 9/12). HVFHV needs more than 30 zones at 50%, so the 40% line applies: 43 zones (38 standing, 5 seasonal: Upper East Side South 11/12, East Harlem North 10, Fort Greene 10, Mott Haven/Port Morris 8, Gramercy 7). Other day-part list sizes (yellow 15-18 zones; HVFHV 33-51 zones at 40%) and standing/seasonal counts: `q1_guidance_lists.csv` and the log. Jaccard of the monthly lists against the full-period list: all hours yellow 0.889-1.000 (mean 0.963), HVFHV 0.889-0.977 (mean 0.940); the lowest value of any day-part list is 0.821 (`q1_monthly_jaccard.csv`).

Takeaway: HVFHV pickups are about 3.6 times more spread out across zones than yellow; airports lead HVFHV and JFK leads yellow's airports; the lists are mostly stable across months.
Limitations: pickup counts favour large zones; no duplicate removal; naive timestamps assumed local; partial weeks at the ends of the period are resampled as whole blocks; n50/n80 are integers, so the CIs are discrete and can be zero width; trip count is not earnings.

## 4. Q2: where airport trips end

Method: share of valid-destination trips per destination zone for each airport; top-5 share versus the all-hours top-5 pickup share of the service; week-block bootstrap with the top 5 re-selected in every replicate, same weeks for airport and overall values; Holm over 6 pairs. Script `pipeline/run_q2.py`, log `outputs/logs/q2.log`.
Charts: `outputs/q2/q2_airport_top10_destinations.png`, `q2_top5_airport_vs_overall.png`. Data: `outputs/q2/q2_airport_top5_vs_overall.csv`, `q2_airport_top10_destinations.csv`.

| Service | Airport | Valid dest. trips | Excluded invalid dest. | Same-airport dest. | top5_airport | top5_overall | delta (pp) [95% CI] | Ratio [CI] | Holm p | Decision (point estimate rule) |
|---|---|---|---|---|---|---|---|---|---|---|
| Yellow | Newark | 6,109 | 224 | 5,969 | 98.23% | 19.64% | +78.59 [78.18, 79.11] | 5.00 [4.95, 5.06] | 0.003 | name destinations (see note) |
| Yellow | JFK | 1,767,662 | 88,951 | 90,980 | 16.22% | 19.64% | -3.42 [-3.73, -3.14] | 0.83 [0.81, 0.84] | 1.000 | do not name |
| Yellow | LaGuardia | 1,162,965 | 20,438 | 23,879 | 18.58% | 19.64% | -1.06 [-1.72, -0.44] | 0.95 [0.91, 0.98] | 1.000 | do not name |
| HVFHV | Newark | 11 | 6 | 7 | n/a | 7.17% | too small (under 1,000 trips) | n/a | n/a | no decision |
| HVFHV | JFK | 3,220,341 | 813,005 | 72,235 | 11.71% | 7.17% | +4.54 [4.25, 4.83] | 1.63 [1.59, 1.68] | 0.003 | name destinations |
| HVFHV | LaGuardia | 4,282,783 | 659,634 | 10,909 | 15.72% | 7.17% | +8.55 [7.99, 9.07] | 2.19 [2.11, 2.27] | 0.003 | name destinations |

Top-5 destinations: yellow JFK: JFK itself, Times Sq/Theatre District, Flushing Meadows-Corona Park, Midtown South, Clinton East. Yellow LaGuardia: Times Sq/Theatre District, Midtown Center, Midtown South, Midtown East, Midtown North. HVFHV JFK: Times Sq/Theatre District, JFK itself, South Ozone Park, Midtown South, Baisley Park. HVFHV LaGuardia: Times Sq/Theatre District, Midtown South, Midtown Center, Midtown East, Midtown North. (Full top 10 with shares: `q2_airport_top10_destinations.csv`.)
Note for the human: yellow Newark passes the rule only because 97.7% of its 6,109 valid trips end in Newark Airport itself; the rule is applied as written, so this reads as a rule result, not a destination pattern. Same-airport destinations are kept per plan; for JFK and LaGuardia they are in the top 5 for JFK (yellow rank 1, HVFHV rank 2). Also note the HVFHV airport destination exclusions are large (about 20% of JFK and 13% of LaGuardia pickups end at invalid IDs 264/265).

Takeaway: at the point estimate, only HVFHV airport trips (JFK, LaGuardia) and yellow Newark are more concentrated than overall pickups; yellow JFK and LaGuardia trips are less concentrated.
Limitations: the top 5 is chosen on the same data it is measured on, so the point estimate is biased upward (not corrected; re-selection per replicate widens the CI only partly); destination zone is where passengers go, not drivers; the overall top-5 share depends on airports being in the data; Holm family kept at 6 including the too-small pair.

## 5. Q3: weekday and weekend shape of the day

Method: day-level night share (hours 22-04) by pickup date; weekday = Mon-Fri minus the 11 federal holidays; weekend = Sat-Sun; per month gap_m (pooled), spread_m (widest difference among Mon, Tue, Wed, Thu pooled night shares), one-sided Welch test on day-level shares with Hedges g, day-level bootstrap inside month x day-of-week cells (resampling in DOW cells instead of whole day types because spread_m needs the DOW cells), Holm over 24 tests, pooled regression with month fixed effects and HC3. Script `pipeline/run_q3.py`, log `outputs/logs/q3.log`.
Charts: `outputs/q3/q3_hourly_profile.png`, `q3_monthly_night_share.png`. Data: `q3_monthly_decision_primary.csv`, `q3_monthly_sensitivities.csv`, `q3_pooled_regression.csv`, `q3_hourly_profile.csv`, `q3_day_level_night_share_primary.csv`.

Days: 365 per service (2025-10-01 to 2026-09-30): 250 weekdays, 104 weekend days, 11 holiday weekdays excluded. No zero-trip days. All in-month trips are used (pickup time only): yellow 46,494,334, HVFHV 253,409,771.

Decision rule result: in all 12 months gap_m > 0 and gap_m > spread_m for both services, so the rule gives "separate night-hour guidance" for yellow and for HVFHV (primary variant).

| Service | gap_m range (pp) | spread_m range (pp) | Smallest margin gap-spread (pp) [95% CI] | Pooled weekend effect (pp) [95% CI] |
|---|---|---|---|---|
| Yellow | 10.08 (Dec 2025) to 16.02 (Mar 2026) | 2.78 to 5.81 | 4.27 [1.78, 6.09] (Dec 2025) | 13.12 [12.36, 13.87] |
| HVFHV | 9.12 (Apr 2026) to 11.10 (Nov 2025) | 1.08 to 2.72 | 6.57 [3.42, 7.88] (Dec 2025) | 10.16 [9.63, 10.69] |

Weekday night share is 13.0-15.9% (yellow) and 16.2-18.5% (HVFHV); weekend 25.6-29.3% (yellow) and 26.3-28.5% (HVFHV) (monthly table in the log). No month's margin CI includes 0. All 24 Welch tests are significant after Holm (largest Holm p = 0.00045; Hedges g from 2.75 to 7.88). Monthly gap CIs and Welch day-average CIs are in the CSV.

Sensitivities (months passing both conditions out of 12; `q3_monthly_sensitivities.csv`, log q3):
- S1 holidays as ordinary days: 12/12 for both services. Pooled effect 12.87 pp yellow, 9.88 pp HVFHV.
- S2 hour 5 in night: 12/12 for both. Pooled 13.06 (yellow), 9.97 (HVFHV).
- S3 literal (hours 0-4 assigned to the previous date, Mon-Fri vs Sat-Sun of the assigned date): yellow gap > spread in 4/12 months, HVFHV 9/12; gap > 0 in 12/12. Pooled 4.57 pp yellow [2.76, 6.38], 3.97 pp HVFHV [2.73, 5.21].
- S3 intent (hours 0-4 assigned to the previous date, Fri and Sat nights = "weekend", Sun-Thu = "weekday"): yellow 12/12 pass; HVFHV 11/12 (Dec 2025 gap 7.25 pp vs spread 8.30 pp). Pooled 13.31 pp yellow, 9.65 pp HVFHV.
- Ambiguity for the human: the plan's S3 text says "hours 0-4 assigned to the previous calendar day, so Friday night to Saturday morning counts as a weekend night". Taken literally, that assignment puts Saturday 0-4 into Friday (a weekday). I ran both readings (labelled as such) and did not choose. S3 is reported next to, not instead of, the primary result.

Takeaway: weekend days have about 10-16 percentage points more of their trips at night than weekdays, far above normal Mon-Thu variation, under the 02 rule.
Limitations: naive timestamps assumed local time; DST days (2025-11-02, 2026-03-08) kept on wall-clock hours; days are treated as independent (weekly rhythm and autocorrelation not modelled); spread_m is a max-minus-min over 4 cells of 3-5 days, which is biased upward, so the rule is demanding; the gap bootstrap CIs use few days per cell; one-sided p-values in the CSV are shown as raw and Holm values.

## 6. Q4: share of trips touching the Congestion Relief Zone list

Method: share = trips with valid PU and valid DO where either end is one of the 38 IDs, divided by trips with valid PU and DO; Jan-Sep of 2023, 2024, 2026; week-block bootstrap per period (40 weeks each, periods independent); Holm over 2 services. Script `pipeline/run_q4.py`, log `outputs/logs/q4.log`.
Charts: `outputs/q4/q4_share_by_year.png`, `q4_monthly_share.png`, `q4_top15_gains_outside_zone.png`. Data: `q4_share_results.csv`, `q4_monthly_share.csv`, `q4_sensitivity_S4.csv`, `q4_zone_id_check.csv`, `q4_fee_crosscheck.csv`, `q4_fee_share_by_pickup_zone_2026.csv`, `q4_supplementary_zone_share_change.csv`, `q4_supplementary_top15_gains_losses.csv`, `q4_neighbour_zone_share_change.csv`.

Zone-ID check: in all service-year-field combinations, no ID outside the lookup and no null (share 0.0). The 0.1% stop rule did not trigger. This shows IDs are valid; it cannot show that zone meaning is unchanged.

| Service | 2023 | 2024 | 2026 | Delta_drift (2024-2023), pp [CI] | Delta_main (2026-2024), pp [CI] | abs(main) - abs(drift), pp [CI] | Relative change main [CI] | Holm p (main < 0) | Rule |
|---|---|---|---|---|---|---|---|---|---|
| Yellow | 73.83% [73.47, 74.20] | 73.65% [73.31, 74.01] | 71.67% [70.98, 72.36] | -0.18 [-0.70, 0.33] | -1.99 [-2.77, -1.23] | +1.81 [0.74, 2.60] | -2.70% [-3.76, -1.67] | 0.001 | real shift: review |
| HVFHV | 36.43% [36.07, 36.78] | 34.74% [34.37, 35.06] | 30.48% [30.07, 30.87] | -1.69 [-2.18, -1.19] | -4.26 [-4.80, -3.75] | +2.57 [1.73, 3.46] | -12.26% [-13.71, -10.86] | 0.001 | real shift: review |

Hypothesis (share fell 2024 to 2026): supported for both services at alpha = 0.05 (raw one-sided p = 0.0005, the minimum for B = 2000). Both margin CIs exclude 0.
Excluded trips (invalid ID at either end): yellow 1.74% (2023), 1.05% (2024), 0.68% (2026); HVFHV 4.07%, 4.12%, 4.50%. Counts in `q4_share_results.csv`. S4 (all trips as denominator): yellow 72.90%, 73.22%, 71.40%; margin +1.50 pp [0.70, 2.20]; HVFHV 36.41%, 34.71%, 30.69%; margin +2.33 pp [1.47, 3.23]; the decision is unchanged ("real shift") for both.
Monthly view (`q4_monthly_share.csv`): yellow 2026 is 69.3-70.6% in Jan-May, then 72.7% (Jun), 74.9% (Jul), 74.7% (Aug), 73.2% (Sep), against 2024 Jul/Aug 75.0%/74.4%. HVFHV 2026 is 29.6-31.6% in every month, below every 2024 month (33.7-35.4%). So the yellow drop is concentrated in Jan-May 2026.

Fee cross-check (Oct 2025 - Sep 2026; `q4_fee_crosscheck.csv`): no null fees.
- Yellow: 33,517,577 trips with fee > 0; (i) share of fee trips with an in-zone end 95.98% [95.93, 96.03]; (ii) share of in-zone trips with a fee 97.07% [96.35, 97.67].
- HVFHV: 82,792,577 trips with fee > 0; (i) 94.35% [94.27, 94.43]; (ii) 99.06% [98.97, 99.14].
- Neither (i) is below 80%, so the flag is not raised. Zone level (2026 pickups): no zone in the list has a fee share under 50%. Outside the list with a fee share above 50%: yellow 9 zones (including Central Park 59.9%, Lincoln Square East 59.0%, Lincoln Square West 54.1%, Upper East Side South 52.3%, Lenox Hill West 50.7%, DUMBO 52.2%, LaGuardia 50.2%, and two island zones with 9 and 22 pickups); HVFHV 7 zones (Central Park 62.8%, Lincoln Square East 68.4%, Lincoln Square West 63.3%, Upper East Side South 64.4%, Lenox Hill East 53.4%, Lenox Hill West 58.1%, Governor's Island 29 pickups). Membership not changed (E3). These zones are mostly the geometry-based neighbours.

Supplementary (outside-zone share changes 2024 to 2026, valid IDs; `q4_supplementary_top15_gains_losses.csv`):
- Largest yellow pickup-share gains: Central Harlem North (+0.21 pp), Central Harlem (+0.21), Washington Heights South (+0.18), Williamsburg North (+0.18), East Harlem South (+0.17). Largest yellow losses: JFK (-0.94), LaGuardia (-0.69), Central Park (-0.36), Lincoln Square East (-0.29).
- Largest HVFHV pickup gains: East New York (+0.12), Elmhurst (+0.11), Jamaica (+0.11), Long Island City (+0.08). Largest loss: JFK (-0.21), Lincoln Square East (-0.09).
- Dropoff-side tables are in the CSV and the log.
- Neighbouring zones (geometry, 6 zones): combined yellow pickup share 14.63% to 13.91% (-0.71 pp), dropoff 14.12% to 13.37% (-0.75 pp); HVFHV pickup 3.37% to 3.07% (-0.30 pp), dropoff 3.28% to 3.04% (-0.24 pp). Per zone (`q4_neighbour_zone_share_change.csv`): yellow Lenox Hill East and Lincoln Square West gained slightly (+0.04, +0.06 pp pickups); all other neighbour changes are negative. For comparison, the 38 list zones' combined pickup share fell 2.53 pp (yellow) and 2.98 pp (HVFHV).

Takeaway: the in-zone share fell between 2024 and 2026 for both services by more than the 2023-2024 change (yellow -1.99 vs -0.18 pp; HVFHV -4.26 vs -1.69 pp); HVFHV was already falling in 2023-2024, so its drift baseline is not flat.
Limitations: one year-to-year drift comparison is a weak baseline; no causal claim (demand, fares, fee, rider mix and working-day mix are not controlled; 29 Feb 2024 and weekday mix not corrected); list membership is the 38 IDs as given and taxi zones do not match the legal boundary; HVFHV invalid-ID exclusion is 4-4.5% and rising; the neighbour set is only 6 zones because no zone across the rivers touches the list; zone ID meaning across years is not verifiable; duplicates not removed.

## 7. Deviations, flags and suggestions for the human (not done)

- The `.gitignore` does not cover `outputs/cache/`; keep it out of commits.
- Yellow Newark Q2 result is driven by Newark-to-Newark trips (see Q2).
- S3 wording ambiguity (see Q3); both readings reported.
- Q3 bootstrap resamples days inside month x day-of-week cells (plan says inside month and day type); reason given in Q3.
- Q2 pair HVFHV Newark: p blanked, still counts in the Holm family of 6.
- The aggregate stage log (`outputs/logs/aggregate.log`) prints a per-file line with timing; step 1 and step 2 logs are in `outputs/logs/step1.log` and `step2.log`.
- Heat-table figures (`q1_standing_seasonal_*.png`) have the suptitle overlapping the panel titles; cosmetic only.
- Optional extra not in the plan (suggestion only): a pre-2023 drift baseline for Q4.
