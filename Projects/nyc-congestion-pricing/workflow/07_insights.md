Author: human
Status: final

# 07 Insights

## I1

### Claim
For yellow taxis, a zone list is a workable form of driver guidance. For high-volume app services (HVFHV), demand is spread over too many zones for a list to work well.

### Evidence (numbers and where they are)
- Number of zones needed to cover 80% of pickups (n80): yellow 36, HVFHV 128. The difference is 92 zones, 95% CI [91, 93]; the ratio is 3.56. (05_analysis.md, section 3 (Q1); 06_validation.md: PASS)
- Top-5 zones hold 19.64% of yellow pickups and 7.17% of HVFHV pickups. (06_validation.md, Q1 table: PASS)
- The guidance list is 17 zones for yellow (covers 50% of trips) and 43 zones for HVFHV (covers only 40%). (06_validation.md: PASS)
- The lists are stable over time: month-to-month overlap (Jaccard) averages 0.96 for yellow and 0.94 for HVFHV. (06_validation.md: PASS)
- Key-number reproduction by me: yellow valid trips 46,415,189, n50 = 17, n80 = 36, all equal to 05. (see Notes)

### Interpretation
A short, fixed zone list can cover half of yellow demand, and because it barely changes from month to month it does not need frequent updates. For HVFHV, a 50% list would need more than 30 zones, so the rule lowered the target to 40%, which already takes 43 zones; a different form of guidance is needed. I did not test which form. Limit: this counts pickups only; it does not look at driver earnings or waiting time.

## I2

### Claim
Airport trips are more concentrated than average only for app-service (HVFHV) trips from JFK and LaGuardia, where the pre-set rule supports a "where airport passengers go" guide; for yellow taxis from JFK and LaGuardia the rule does not. Even for HVFHV, the top-5 destinations cover only about 12-16% of trips.

### Evidence (numbers and where they are)
- Share of airport trips going to their top-5 destinations, compared with the top-5 share of all trips (yellow 19.64%, HVFHV 7.17%):
  - HVFHV JFK 11.71% (+4.54 pp), HVFHV LaGuardia 15.72% (+8.55 pp): rule result "name destinations".
  - Yellow JFK 16.22% (-3.42 pp), yellow LaGuardia 18.58% (-1.06 pp): rule result "do not name".
  (05_analysis.md, section 4 (Q2); 06_validation.md: PASS)
- For LaGuardia, the top-5 destinations are all Midtown zones in both services. (05_analysis.md, section 4 (Q2))
- An out-of-sample check by the validator (top 5 chosen on odd weeks, measured on even weeks) changed no decision; the upward bias is about 0.1-0.3 pp. (06_validation.md, section 5)

### Interpretation
A destination guide is supported for HVFHV at JFK and LaGuardia, and for LaGuardia it would mostly say "Midtown". It would help with only a minority of airport trips, since the top-5 destinations cover 12-16%. For yellow taxis the data does not support such a guide at these two airports. Limits: yellow Newark passes the rule (98.23%) only because 97.7% of its 6,109 valid trips end at Newark Airport itself, so I do not read it as a destination pattern; HVFHV Newark has 11 valid trips and no decision. About 20% of HVFHV JFK pickups and 13% of LaGuardia pickups end at unknown zone IDs (264/265) and are excluded. Trips that end at the same airport are kept as planned.

## I3

### Claim
Night trips (22:00-04:59) are a much larger share of weekend days than of weekdays, in every one of the 12 months, for both services.

### Evidence (numbers and where they are)
- Night share, weekday vs weekend: yellow 13.0-15.9% vs 25.6-29.3%; HVFHV 16.2-18.5% vs 26.3-28.5%. (05_analysis.md, Q3 section; 06_validation.md: PASS)
- The weekend-weekday gap (yellow 10.08-16.02 pp, HVFHV 9.12-11.10 pp) is larger than the day-to-day spread inside a day type (yellow 2.78-5.81 pp, HVFHV 1.08-2.72 pp) in 12 of 12 months for both services.
- Pooled weekend effect with month fixed effects: yellow +13.12 pp [12.36, 13.87], HVFHV +10.16 pp [9.63, 10.69]. (06_validation.md: PASS)
- The weakest month is December 2025; its gap still exceeds the spread (yellow margin 4.27 pp [1.78, 6.09], HVFHV 6.57 pp [3.42, 7.88]).
- Sensitivity S3 (what counts as a weekend night): I chose the reading "a night that starts on Friday or Saturday". With it, the gap exceeds the spread in 12 of 12 months for yellow and 11 of 12 for HVFHV. The literal wording of the plan gives 4 and 9 months. See `05a_human_review.md`.

### Interpretation
The data supports separate night guidance for weekdays and weekends. It does not show whether drivers already know this; that depends on who the guidance is for, and I decide it in 09. Limits: day-level shares are not independent (weekly rhythm), although a non-parametric test agrees in 24 of 24 month-service tests. The bootstrap resamples month x day-of-week cells instead of month x day type, which differs from the plan text (a disclosed deviation; the validator reproduced the intervals with the same unit).

## I4

### Claim
After congestion pricing, the share of trips touching the congestion zone fell by about 2 pp (yellow) and 4 pp (HVFHV) compared with 2024, more than the 2023-2024 change, but the lost share did not move to one place outside the zone. This does not show that the fee caused it.

### Evidence (numbers and where they are)
- Share of trips with a pickup or dropoff in the 38 zones, 2024 to 2026: yellow 73.65% to 71.67% (-1.99 pp; relative -2.7%), HVFHV 34.74% to 30.48% (-4.26 pp; relative -12.3%). (05_analysis.md, section 6; 06_validation.md: PASS)
- Margin over the 2023-2024 baseline: yellow +1.81 pp [0.74, 2.60], HVFHV +2.57 pp [1.73, 3.46]. The decision rule gives "real shift" for both.
- Largest pickup-share gains outside the zone are small: yellow +0.21 pp (Central Harlem North), HVFHV +0.12 pp (East New York). The six neighbouring zones together lost share (yellow -0.71 pp, HVFHV -0.30 pp), while the 38 zone list lost 2.53 pp and 2.98 pp. (05_analysis.md, section 6, Supplementary; 06_validation.md: PASS)

### Interpretation
The two services behave differently. The yellow drop is concentrated in January-May 2026; in June-September it is close to 2024 and to the baseline. HVFHV is lower than 2024 in every month, but its baseline was already falling (-1.69 pp). Gains outside the zone are spread thinly: in yellow they are in upper Manhattan and Williamsburg, in HVFHV in outer-borough hubs such as East New York, Elmhurst and Jamaica. So this analysis finds no obvious new hotspot. Limits: these are shares, not trip counts. It is a before/after comparison with one baseline year pair, and demand, fares, rider mix and weekday mix are not controlled.

## Notes

- Key-number reproduction: I recomputed the Q1 yellow valid trip count with DuckDB on the 12 monthly files. A first query that merged the files and then applied the date range gave 46,415,358 (169 more). Counting each file's own month only gave 46,415,189, equal to 05. The difference came from rows whose pickup date is in a neighbouring month. n50 = 17 and n80 = 36 matched. I did not reproduce the HVFHV or Q2-Q4 numbers myself.
- Not verified (also not by the validator): that timestamps are New York local time, that zone IDs keep the same meaning across 2023-2026, and the PNG charts.
- Yellow rows with the same pickup time, dropoff time and zones are 1.14% of yellow trips. They were kept; removing them changes the Q4 yellow margin from +1.81 to +1.89 pp.