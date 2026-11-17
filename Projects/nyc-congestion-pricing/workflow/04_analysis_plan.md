Author: ai/analyst
Status: plan for human review (Phase A). No code has been written and no analysis has been run. The approval line is added by the human only.

# 04 Analysis Plan: Q1-Q4

Inputs: `02_questions.md` (final, human), `03_data_plan.md` (GO, human decisions at Gate 1), `data_manifest.json` (empty, to be filled in step 1). Questions, hypotheses and decision rules are not changed here. Where 02 leaves a detail open (holidays, edge zones, tie rules), this plan fixes it before any result.

## 0. Global rules (apply to every question)

**Services.** Every question runs separately for yellow taxi and for HVFHV ("Uber/Lyft"). Combined views are context only. HVFHV is used as delivered (all licence holders in the file). The `hvfhs_license_num` field is not used. Reason: 02 defines the service as the high-volume FHV file.

**Files used (30 per service, 60 total).**
- Q1-Q3: Oct 2025 - Sep 2026 (12 months).
- Q4: Jan-Sep 2023, Jan-Sep 2024, Jan-Sep 2026 (27 months).
- Union: 9 + 9 + 3 + 9 = 30 files per service.

**Randomness and software.**
- Seed 42 for every bootstrap.
- B = 2000 replicates; percentile 95% CI.
- Library versions (pyarrow 26.0.1 and others) are recorded in `05_analysis.md`.

**Processing.**
- One file at a time, only the needed columns (pyarrow column pruning), aggregate immediately and keep the aggregates.
- Reason: HVFHV months have about 20M rows (03, human sample).
- Per 02, months are reduced only if processing fails. Any reduction is written into `05_analysis.md` before results are computed.

**Zone validity.**
- Valid ID = ID present in `taxi_zone_lookup.csv` and not "Unknown" or "Outside of NYC" in the lookup. The expected IDs are 264 and 265. Step 3 confirms this from the lookup before use.
- Null IDs are invalid.
- A trip with an invalid ID is excluded from the question that needs that ID.
- The count and share of excluded trips are reported per service, per month and per question. This is required by 02.

**Period validity.** A trip counts only if its pickup datetime falls in the same calendar month as the file. Provider date errors are dropped and counted. Reason: the TLC page warns about them (03).

**Missing values and outliers (default for all questions).**
- Every metric is a count or a share of counts. The plan does not filter on fare, distance, duration or passenger count. These fields are not used, and filtering on them would silently change what "trip" means in 02.
- Missing values: a trip is dropped from a question only if a field that the question needs is null or invalid (rules above). Nulls in fields the question does not use are ignored.
- Outliers: there is no statistical trimming. The only removals are invalid IDs, out-of-month timestamps, and null required fields.
- Duplicates are not removed. The data has no trip key, and any dedup rule would be a guess. This is listed as a limitation.

**Inference defaults (each question restates its own).**
- alpha = 0.05.
- A directional hypothesis in 02 is tested one-sided. Its CI is two-sided 95%.
- Multiple comparisons: Holm-Bonferroni within each question's confirmatory family. No correction across questions, because each question feeds a different decision.
- With tens of millions of trips, p-values are nearly always tiny. So the plan reports effect size and CI first, and p-values only as support.
- **The decision rules in 02 are applied exactly as written, on point estimates.** The CI or p-value is reported beside each decision to show whether it is distinguishable from sampling noise. It does not replace the rule. If a decision sits inside its CI, it is flagged for the human.
- Bootstrap unit: the calendar week (Mon-Sun block) within the period, resampled with replacement, per service. Reason: trips within a day and days within a week are strongly dependent, so trip-level or day-level resampling would give CIs that are too narrow. Q3 uses days (see Q3).

**Outputs for each question.**
- One PNG per chart with an aggregated CSV/JSON of the same name beside it (CLAUDE.md).
- Figure-returning plot functions in `pipeline/visualize`, no `plt.show()`.
- A why-comment for every decision.
- No raw data is exported or committed.

## 1. Step 1: schema and file check (before any aggregation)

Metadata only: no row data is read in this step.

**Procedure.**
- For each of the 60 Parquet files, use `pyarrow.parquet.read_schema` and `ParquetFile(...).metadata` to record column names, dtypes, timestamp unit and timezone, and `num_rows`.
- Compute the sha256 checksum and file size of each file.
- Write one entry per file into `data_manifest.json`: name, `file_path`, source URL pattern (TLC CloudFront, 03), download date (the human's value from 03: 2026-11-13), `row_count`, checksum, and a note "no explicit licence on TLC page; terms not found, checked 2026-11-13" (03, item 4).
- Add `taxi_zone_lookup.csv` and the two zone-list files with the same fields.
- Output a table of distinct schemas and which files share each one.

**Required fields.**

| Field | Yellow | HVFHV | Needed by | Required in |
|---|---|---|---|---|
| Pickup datetime | `tpep_pickup_datetime` | `pickup_datetime` | Q1-Q4 | all 30 files per service |
| Dropoff datetime | `tpep_dropoff_datetime` | `dropoff_datetime` | none directly (Q4 uses zones, not times) | recorded only |
| Pickup zone | `PULocationID` | `PULocationID` | Q1-Q4 | all 30 |
| Dropoff zone | `DOLocationID` | `DOLocationID` | Q2, Q4 | all files used by Q2 (Oct 2025 - Sep 2026) and Q4 (2023, 2024, 2026) |
| Congestion fee | `cbd_congestion_fee` | `cbd_congestion_fee` | Q4 cross-check only | Oct-Dec 2025 and Jan-Sep 2026 (12 files per service) |

Dropoff datetime is not used by Q1-Q4 metrics. It is checked because 02 lists it as Q4 data. Its absence does not stop anything. It is only reported.

**Expected, not an error.** `cbd_congestion_fee` is absent from the 2023 and 2024 files (human check in 03).

**Dtype requirements.**
- Pickup datetime must be a timestamp type. A string or integer type is a stop (see below).
- Location IDs must be integer-like (nullable int allowed).
- Timezone: if the timestamp has a timezone, record it. The wall-clock hour in New York is what Q1 and Q3 need. If the timezone is anything other than a New York zone (or UTC with a documented offset), stop and ask. If timestamps are naive, assume local New York wall clock, as the TLC does. This is not verifiable from the schema and is listed as an assumption.

**Stop conditions (analysis halts and the analyst reports to the orchestrator; there is no silent renaming or aliasing).**
1. Any of `pickup datetime`, `PULocationID` is missing from any of the 30 files of a service. Stop for all questions on that service.
2. `DOLocationID` is missing from any file used by Q2 or Q4. Stop Q2 and Q4 for that service. Q1 and Q3 may continue only after the human confirms.
3. A required field exists under a different name (for example lower case or snake case). Stop and report the exact name. Only the human changes the plan; the analyst does not map names on its own.
4. A required field has the wrong dtype (string, float with fractions in IDs, or a non-timestamp pickup column).
5. `cbd_congestion_fee` is missing from any Oct 2025 - Sep 2026 file. The Q4 fee cross-check is then not run for that file. The Q4 main metric is unaffected. This is reported, not a stop for Q1-Q4 results. If it is absent from all 24 files, the cross-check is marked "not possible" and the human is told.
6. A file is missing, unreadable, or has zero rows.
7. The file count is not 30 per service, or the months do not match the list in section 0.
8. The timezone case above.

**Flag but do not stop.**
- Any other column difference between files.
- Any month whose row count differs by more than 30% from its service median. The human is told.
- Row counts far outside the human's sample ranges (yellow about 3.0-3.7M, HVFHV about 19.7-20.9M per month).

**Report.** The result of step 1 (pass or stop, per field per service) is the first section of `05_analysis.md`, with the script path and its log.

## 2. Step 2: lookup, zone lists, zone-ID check

**Lookup.** Read `taxi_zone_lookup.csv`. Confirm columns `LocationID`, `Borough`, `Zone` exist (stop if not). Confirm which IDs are labelled "Unknown" or "N/A" or "Outside of NYC" and fix the invalid list from this.

**Airport zones (Q1, Q2).** Fixed by the human in 03: IDs 1 (Newark Airport), 132 (JFK Airport), 138 (LaGuardia Airport). Step 2 checks that these IDs and names match the lookup. If they do not match, stop.

**Congestion Relief Zone list (Q4).** The human's saved file of the MTA CBD taxi zones (38 rows, 03 item 5).
- The analyst locates it. If the file cannot be found in the project, stop and report; do not rebuild the list.
- The file must have 38 distinct IDs, all present in the lookup. Otherwise stop.
- Print the zone names beside the IDs in the log, so the human can check them.

**Edge-zone rules (fixed here, before results).**
- E1. Membership = the 38 IDs as given, with no additions and no removals. A zone is wholly inside or wholly outside, even if the taxi zone only partly lies within the legal boundary. Reason: 03 says taxi zones do not match the legal boundary exactly, and a single, stated rule avoids choosing zones after seeing results.
- E2. IDs 264 and 265 are never inside. They are excluded as invalid.
- E3. Membership is frozen. The fee-based check in Q4 can flag zones that look misclassified. It does not change the list.

**Zone-ID check across years (02, Q4).**
- For each file used, take the set of distinct `PULocationID` and `DOLocationID` values.
- Report IDs that are not in the lookup, per service per year.
- Stop Q4 if any ID outside the lookup (other than null) accounts for more than 0.1% of a year's trips. Otherwise, count them as invalid and report them.
- Limit: this shows that IDs are valid. It cannot show that a zone's boundary or meaning is unchanged. No evidence of a change was found (03). This is stated in Q4 limitations.

## 3. Q1: pickup zones by part of the day, and concentration

**Metric definition.**
- Day-part by pickup hour (local wall clock), inclusive: overnight hours 0-5, morning 6-9, midday 10-15, evening 16-19, night 20-23. This reads 02's "00-05" as hours 00:00-05:59.
- Trips per `PULocationID` per day-part per service over Oct 2025 - Sep 2026, and per month.
- Ranked by trips. Cumulative share of trips by rank.
- n50 and n80 = the smallest number of zones whose cumulative share reaches 50% and 80% (all hours, and for each day-part).
- Top-5 pickup share for the whole period (all hours) per service (also used by Q2).
- Share of valid zones that have at least one trip.

**Method and why.**
- Descriptive ranking and a cumulative share curve (Lorenz-style).
- Reason: the decision (which zones to list) is a ranking decision. No model is needed.
- Guidance list per service and day-part = the smallest set of zones covering 50% of trips. If it has more than 30 zones, the line is 40% (02 rule). The same cut-off is applied to every month's list for that service and day-part.
- Standing and seasonal: a zone in the full-period list is "standing" if it is in the list of every one of the 12 monthly lists. Otherwise it is "seasonal". Report the Jaccard overlap of each monthly list with the full-period list.
- Ties at the cut-off: rank by zone ID ascending, and note any tie. Unlikely with counts this large.

**Hypotheses.**
- (a) Airport zones (1, 132, 138) are among the top 5 pickup zones for the whole period, for both services. This is a rank check, with no test. Also report in how many of the 12 months each airport is in the monthly top 5.
- (b) More zones are needed for 80% of HVFHV trips than for 80% of yellow trips, i.e. n80(HVFHV) > n80(yellow).

**Tests, effect size and CI.**
- Hypothesis (b): week-block bootstrap per service, then the difference d = n80(HVFHV) - n80(yellow).
- Effect size: d in zones and the ratio n80(HVFHV) / n80(yellow). 95% percentile CI. One-sided bootstrap p-value for d > 0.
- n50 is reported in the same way, as a descriptive value (no p-value).
- Each n50, n80 and top-5 share per service also gets a 95% week-block bootstrap CI.
- alpha = 0.05. The confirmatory family has one test, so no correction is needed. n50, the day-part values and (a) are descriptive.

**Assumptions.**
- One row = one trip (TLC page, 03; not verified in the dictionary).
- n80 is comparable across services because both draw on the same set of zones (lookup).
- Pickup counts favour large zones (02, known limit). No normalisation by zone size is applied, because no area or population field is in the data.

**Data fields.** Pickup datetime, `PULocationID`, lookup (`LocationID`, `Zone`, `Borough`).

**Missing and outlier policy.** Section 0. Exclusions: null or invalid `PULocationID`, null or out-of-month pickup datetime. Counts reported.

**Expected charts.**
1. Per service, a ranked horizontal bar chart of the top 10 zones for each day-part (small multiples, airports highlighted).
2. Cumulative share curve against zone rank, both services on one panel, with n50 and n80 marked.
3. A standing and seasonal heat table (zones by month, in or out of the list), per service for the whole-day or each day-part list.

## 4. Q2: where airport trips end

**Metric definition.**
- For each airport zone (1, 132, 138) and each service, among trips with `PULocationID` = that airport and a valid `DOLocationID`: the share going to each destination zone.
- top5_airport = combined share of the 5 largest destination zones.
- Comparison value top5_overall = the combined share of the 5 largest pickup zones among all valid-pickup trips, for the whole period, per service (from Q1, all hours). This fixes what 02 means by "the top 5 pickup zones hold of all trips".
- Difference delta = top5_airport - top5_overall (percentage points).
- Trips with an invalid destination (264, 265 or null) are excluded from the airport's denominator and counted.
- An airport trip with destination equal to the same airport is kept (it is a valid zone). Its count is reported.

**Method and why.**
- Descriptive shares with a bootstrap CI.
- Reason: 02 needs a share comparison, not a model.
- The top-5 set is re-selected inside every bootstrap replicate. Reason: the top 5 are picked from the same data they are measured on, which biases the share upward. Re-selection per replicate captures part of this selection effect in the CI. The point estimate is still not bias-corrected, and this is stated as a limitation.

**Decision rule (02, unchanged).** If top5_airport > top5_overall, airport guidance names those destination zones. Otherwise it does not. Applied to each airport and service on the point estimate.

**Tests, effect size and CI.**
- One-sided week-block bootstrap for delta > 0, where days (weeks) are resampled jointly for the airport and the overall values.
- Report delta in percentage points, the ratio top5_airport / top5_overall, and a 95% CI.
- Family = 6 comparisons (3 airports x 2 services). Holm correction, alpha = 0.05.
- Minimum size: an airport-service pair with fewer than 1,000 valid trips in the period is reported descriptively only, with no decision. Reason: below about 1,000 trips the standard error of a share near 0.3 is above about 1.5 percentage points. This is likely for Newark (ID 1). Such pairs are marked "too small".

**Assumptions.**
- The drop-off zone shows where passengers go, not where drivers go next. This is not measured (02).
- Zone 1 may have few trips from these services.

**Data fields.** Pickup datetime (month filter), `PULocationID`, `DOLocationID`, lookup.

**Missing and outlier policy.** Section 0. Exclusions: null or invalid `DOLocationID` for the airport shares. Counts reported per airport.

**Expected charts.**
1. Per service, a horizontal bar chart of the top 10 destination zones for each airport, with the top-5 cumulative share labelled.
2. A dot chart with CI: top5_airport against top5_overall for each airport and service.

## 5. Q3: weekday and weekend shape of the day

**Metric definition.**
- Unit = calendar day by pickup date (local wall clock). Per service, per day: trips by hour, daily total, and night_share = trips in hours 22, 23, 0, 1, 2, 3, 4 divided by the day's trips. This reads 02's "22:00 to 05:00" as 22:00-04:59 (7 hours); the 05:00 hour belongs to the morning. If the human prefers hour 5 included, say so at the gate.
- Day types: weekday = Mon-Fri, weekend = Sat-Sun.
- Monthly night share per day type = night trips / all trips in that month and day type, pooling days.
- Daily totals: mean trips per day by day type and month.
- Hourly profile: mean trips per hour of day per day type (total trips in the hour / number of days of that type), with a 95% CI across days. A normalised version (share of the day's trips) is shown beside the absolute one.

**Holidays (fixed here, before results).**
- Federal holidays that fall on a Mon-Fri are excluded from the weekday group and from the Mon-Thu comparison. They are not moved to the weekend group. Reason: they behave like weekend days and would blur the contrast. Holidays on Sat or Sun need no change.
- The list is written to a file before computation:

| Date | Holiday |
|---|---|
| 2025-10-13 | Columbus Day |
| 2025-11-11 | Veterans Day |
| 2025-11-27 | Thanksgiving |
| 2025-12-25 | Christmas Day |
| 2026-01-01 | New Year's Day |
| 2026-01-19 | Martin Luther King Jr. Day |
| 2026-02-16 | Presidents Day |
| 2026-05-25 | Memorial Day |
| 2026-06-19 | Juneteenth |
| 2026-07-03 | Independence Day (observed, because 4 July 2026 is a Saturday) |
| 2026-09-07 | Labor Day |

- Sensitivity S1: the same results with holidays left as ordinary calendar days.

**Daylight saving.** Days with 23 or 25 hours (2025-11-02, 2026-03-08) are kept and use the wall-clock hour. The effect on night share is small. It is noted in limitations.

**Method and why.**
- Descriptive profiles plus a day-level comparison.
- Reason: 02's rule compares a weekend-weekday gap with the normal variation between weekdays, so the unit must be a day within a month.
- For each month m and service:
  - gap_m = night_share(Sat-Sun) - night_share(Mon-Fri, holidays removed).
  - spread_m = the largest difference between any two of the four day-of-week night shares Mon, Tue, Wed, Thu in month m. This is the widest "ordinary weekday difference" and the most demanding comparison. It is a choice made here for 02's "difference between two ordinary weekdays".
- Decision rule (02): separate night-hour guidance if, in every one of the 12 months, gap_m > 0 and gap_m > spread_m. Otherwise one version is used. Applied per service.

**Hypothesis test.** H1: night share is higher on weekend days than on weekdays, for each service.

**Tests, effect size and CI.**
- Per month and service: Welch t-test (one-sided, weekend > weekday) on day-level night shares.
  - Effect size: gap_m in percentage points with a 95% CI (Welch).
  - Also Hedges g.
- Day-level bootstrap within month and day type (B = 2000) gives a 95% CI for gap_m - spread_m, to show whether the decision margin is distinguishable from noise. Days, not weeks, are resampled here because the month has only a few weeks per day type.
- Pooled estimate per service: a regression of day-level night share on a weekend indicator with month fixed effects, HC3 standard errors. Effect = coefficient in percentage points with a 95% CI.
- Family for the confirmatory tests = 24 (12 months x 2 services). Holm, alpha = 0.05. The pooled regression is a separate single test per service, so it is not in the family.
- Sensitivity S2: hour 5 included in night (22:00-05:59).
- Sensitivity S3: hours 0-4 assigned to the previous calendar day, so Friday night to Saturday morning counts as a weekend night. This is a different, plausible reading of "night on weekend". It is not part of the 02 rule. It is reported next to the primary result so that the human can judge. If the human does not want it, strike it from the plan at the gate.

**Assumptions.**
- Timestamps are local wall clock (step 1).
- Days are independent enough for a Welch test. Weekly rhythm and autocorrelation are not modelled. The week-block approach used in other questions is not possible with about 8-9 weekend days per month.

**Data fields.** Pickup datetime only.

**Missing and outlier policy.** Section 0. Exclusions: null, out-of-month pickup datetime. Days with zero trips are not expected. If one appears, it is reported and kept as missing, not as 0%.

**Expected charts.**
1. Hourly profile, one line per day type, 2 panels (services), absolute and normalised.
2. Monthly night share by day type (lines or dots, 12 months), with gap_m and spread_m shown, as the direct picture of the decision rule.

## 6. Q4: share of trips touching the Congestion Relief Zone

**Metric definition.**
- A trip is "in zone" if `PULocationID` or `DOLocationID` is among the 38 CRZ IDs (section 2).
- Denominator = trips with valid `PULocationID` and valid `DOLocationID` (so that "neither end in zone" is known). Reason: a trip with an unknown end could be inside, and including it would mix data quality with the zone effect.
- share = in-zone trips / denominator, per service, for the periods:
  - Drift period A: Jan-Sep 2023.
  - Pre period: Jan-Sep 2024.
  - Post period: Jan-Sep 2026.
- Also monthly shares for Jan-Sep of each year.
- Delta_main = share(2026) - share(2024). Delta_drift = share(2024) - share(2023). Both in percentage points.
- Report the excluded-trip share for each period and service, since changes in it can mimic a change in share.

**Method and why.**
- Same-month comparison across years, which avoids seasonality (02).
- Reason: the decision is whether the change exceeds normal year-to-year movement. So the drift baseline is estimated the same way.
- Decision rule (02): if |Delta_main| > |Delta_drift|, treat it as a real shift and review guidance for the zone and neighbouring zones. Otherwise keep current guidance. Applied per service on the point estimates.

**Hypothesis.** The in-zone share fell between Jan-Sep 2024 and Jan-Sep 2026, for both services (Delta_main < 0).

**Tests, effect size and CI.**
- Week-block bootstrap within each period (resample the calendar weeks of the period separately; periods are treated as independent), per service.
- Report:
  - Delta_main and Delta_drift with 95% CIs.
  - |Delta_main| - |Delta_drift| with a 95% CI (the decision margin).
  - The relative change Delta_main / share(2024).
  - One-sided bootstrap p-value for Delta_main < 0.
- Family for the hypothesis = 2 tests (2 services). Holm, alpha = 0.05.
- Limit: the drift baseline is one year-to-year comparison, so it says little about how much the share would normally move. 03 notes this. The result is reported with that limit, plus the monthly lines for each year to show the spread across months.

**Fee cross-check (02).**
- Run on the Oct-Dec 2025 and Jan-Sep 2026 files, on trips with pickup date on or after 2025-01-05 (all of these files qualify).
- Report two proportions per service: (i) of trips with `cbd_congestion_fee` > 0, the share with an in-zone end (02 expects "mostly"); (ii) of in-zone trips, the share with a fee > 0.
- A null fee is treated as "no fee" and counted separately.
- The fee may also apply to trips that only pass through the zone and not to every in-zone trip, so there is no pass or fail threshold. The two shares are reported. If (i) is below 80% for either service, flag it for the human as a sign that the zone list or the fee field does not match. Nothing is changed. Membership stays frozen (E3).
- Edge-zone flag (descriptive): for each lookup zone, the share of its pickups with a fee > 0 in 2026. List the zones inside the CRZ list with a low share (below 50%) and zones outside it with a high share (above 50%).

**Neighbouring zones (02 decision text).**
- Taxi zone adjacency needs the zone shapefile. It is not in the data files, and the plan does not download it.
- Supplementary, descriptive table with no tests: for each zone outside the CRZ list, the change in its share of the service's pickups and of its dropoffs between 2024 and 2026, with the 15 largest gains and losses. Shown with borough.
- The human can pick the neighbouring zones from this table. If the human wants adjacency by geometry, approve the `taxi_zones.zip` URL in 03 (Open item B below).

**Assumptions.**
- Zone IDs mean the same thing in 2023, 2024 and 2026 (partly checked in step 2).
- Other changes in 2023-2026 are not controlled: demand, fares, the fee itself, a changed rider mix, and the change in the number of working days. The result cannot show cause (02).
- The weekday mix of Jan-Sep differs slightly between years (including 29 Feb 2024). This is not corrected, and is listed as a limitation.

**Sensitivity.**
- S4: all trips (including invalid-ID trips) as the denominator. This shows how much the exclusions matter.

**Data fields.** Pickup datetime (month filter), `PULocationID`, `DOLocationID`, `cbd_congestion_fee` (2025 on), lookup, CRZ list file.

**Missing and outlier policy.** Section 0. Exclusions: null or invalid either ID, out-of-month pickup datetime.

**Expected charts.**
1. Grouped bars of the Jan-Sep in-zone share for 2023, 2024 and 2026 per service, with 95% CI, and Delta_main and Delta_drift labelled.
2. Monthly lines (Jan-Sep) of the in-zone share by year, per service.
3. A bar chart of the 15 largest outside-zone gains in the supplementary table.

## 7. Outputs and files

**Written to the project by the analyst in Phase B.**
- `data_manifest.json` (entries per file, from step 1).
- Zone-list and holiday-list files, written before results.
- Aggregated tables and PNG files per question.
- `05_analysis.md`.

**Evidence for every number.** For each number, the script path plus the log or output file that printed it.

**Not committed.** Data files and intermediate aggregates that are too large.

## 8. Assumptions to confirm at the gate

1. Day-part hours are inclusive on both ends: overnight 0-5, morning 6-9, midday 10-15, evening 16-19, night 20-23.
2. Night for Q3 = hours 22-04 (7 hours). Hour 5 is not included. Sensitivity S2 covers the alternative.
3. Q3 assigns night hours to the calendar date of pickup. Sensitivity S3 shows the "previous evening" view and can be removed.
4. Q3 spread_m = the widest difference among Mon, Tue, Wed, Thu in the month.
5. Federal holidays on Mon-Fri are excluded from the weekday group (list in Q3).
6. Q4 membership = the 38 MTA IDs, as given (E1-E3).
7. The Q2 comparison value is the all-hours, whole-period top-5 pickup share.
8. Q2 pairs with fewer than 1,000 trips get no decision.

## 9. Open items and limitations to carry into 05

**Open items for the human.**
- A. The path of the saved CRZ list and the airport list. Step 2 will stop if it cannot find them.
- B. Zone adjacency needs `taxi_zones.zip`. It is not downloaded. Decide whether to add it, or pick neighbours from the Q4 supplementary table.
- C. Terms of use were not found (03). The manifest records this.

**Limitations (all questions).**
- Trip count is not earnings.
- Unmatched or cancelled requests are invisible.
- Zones differ in size.
- Duplicates are not removed.
- Counts of excluded trips are reported.
- The result cannot show that the fee caused a change.
- HVFHV includes all licence holders in the file, not only Uber and Lyft by name.

**Blockers.** None for the plan. All stop conditions are in step 1 and step 2.

## Human decisions at Gate 2 (2026-11-13)
Author of this block: human. The plan text above is unchanged.

Decisions on section 8:
1. Day-part hours are inclusive as written in the plan (overnight 00:00-05:59, morning 06:00-09:59, midday 10:00-15:59, evening 16:00-19:59, night 20:00-23:59).
2. Q3 night = hours 22-04 (22:00-04:59). Hour 5 is not included; S2 covers it.
3. Q3 night hours are assigned to the calendar date of pickup. S3 stays in the plan as a reported sensitivity next to the primary result.
4. Q3 spread_m = the widest difference among Mon, Tue, Wed, Thu in the month.
5. Federal holidays on Mon-Fri are excluded from the weekday group (list in Q3). S1 stays.
6. Q4 membership = the 38 MTA IDs as given (E1-E3).
7. Q2 comparison value = all-hours, whole-period top-5 pickup share.
8. Q2 airport-service pairs with fewer than 1,000 valid trips get no decision.

Open items:
A. Zone lists. Airport zones: IDs 1, 132, 138 (as in 03). Congestion Relief Zone: the file data/MTA_Central_Business_District_Taxi_Zones_20261113.csv; the IDs are in the column "Taxi Zone". Stop if it does not contain 38 distinct IDs.
B. Neighbouring zones (Q4), by geometry. Data: data/taxi_zones.shp (the TLC zone shapefile, with the files beside it). A neighbouring zone = a zone not in the 38-zone list that shares at least one boundary point with any of the 38 zones, using the shapefile geometry as given, with no tolerance. If a zone has no neighbour, report it; do not change the list. Report the change in pickup and dropoff share of the neighbouring zones (2024 to 2026) next to the supplementary table. I installed geopandas 1.2.0, shapely 2.2.0, pyogrio 0.13.0 and pyproj 3.8.0 in the project .venv; the analyst does not install anything.
C. Terms of use: not found, recorded in the manifest (03).

Approved: human