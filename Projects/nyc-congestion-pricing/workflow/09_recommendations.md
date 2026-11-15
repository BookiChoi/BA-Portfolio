Author: human
Status: final

# 09 Recommendations

## R1

### Recommendation
Pilot a fixed pickup-zone list for yellow taxi drivers: give a small group of drivers the 17-zone list that covers 50% of pickups (15 standing zones, 2 seasonal zones), keep a comparison group without it, and measure the effect before any wider rollout. HVFHV is not part of this recommendation.

### Owner (department)
Yellow taxi fleet operations.

### Rationale
Based on I1. The 17-zone list covers half of yellow pickups, while HVFHV needs 43 zones for 40%, so a list fits yellow but not HVFHV. The 08 critique showed that I1 does not prove the list is useful: the stability number is in-sample (it compares each month with a full-period list that contains it), "workable" was never measured, and there are no earnings or waiting-time data. This is why the recommendation is a pilot with a comparison group, and not a rollout. The two seasonal zones (Clinton East 11 of 12 months, Lenox Hill West 9 of 12) should be shown as seasonal.

### My assumptions and values

| Assumption | Unit | Low | Base | High | Basis |
|---|---|---|---|---|---|
| Drivers in the pilot group (the comparison group has the same size) | drivers | 20 | 50 | 100 | My judgment: large enough to compare, small enough to be cheap. No data in this project. |
| Share of pilot drivers who follow the list | % | 30 | 50 | 70 | My judgment: guidance is usually followed only in part. |
| Change in trips per driver-hour for drivers who follow the list | % | 0 | 3 | 8 | My judgment. There are no earnings or waiting-time data here, so the effect is unknown; the low value is 0 on purpose. |
| Length of the pilot | weeks | 8 | 8 | 12 | My judgment: long enough to include several weekends. |

### Success metric (KPI)
Trips per driver-hour, pilot group minus comparison group, measured over the pilot. The rule is set before the pilot: success if the difference is at least +3% and its 95% interval stays above 0; stop the idea if the difference is 0 or below after the full pilot. Second metric: share of the pilot drivers' pickups that fall inside the list zones.

### Risks and trade-offs
- More drivers going to the same zones can lower pickups per driver there (oversupply).
- The list was built on one year of data (Oct 2025 - Sep 2026) and the pilot could miss the seasonal zones if it is short.
- Drivers in the two groups may share the list, which would hide the effect.
- Demand patterns may change (for example after congestion pricing; see I4), so the list needs a refresh rule.
- Trips per driver-hour does not measure earnings; fares are not in this analysis.

## R2

### Recommendation
Add a short weekday-versus-weekend night guide to the onboarding material for new drivers, for yellow taxis and, separately, for app-service (HVFHV) drivers. Before the guide goes out, compute night trip counts per day by day type from the existing data, to check that the higher weekend night share is not only a smaller daytime total.

### Owner (department)
Driver onboarding and training, with the operations team of each service.

### Rationale
Based on I3. Night trips (22:00-04:59) are a much larger share of weekend days than of weekdays (yellow 25.6-29.3% vs 13.0-15.9%; HVFHV 26.3-28.5% vs 16.2-18.5%) in all 12 months, and the gap is larger than the normal day-to-day spread under the primary definition. The data cannot say whether experienced drivers already know this, so I aim the guide at new drivers, where the cost is low. The 08 critique raised that a share is not a count: a larger weekend night share can come from fewer daytime trips. The first step of this recommendation (night trip counts per day) answers that point before anything is sent. The guide does not name zones, because Q3 measured the shape of the day only.

### My assumptions and values

| Assumption | Unit | Low | Base | High | Basis |
|---|---|---|---|---|---|
| New drivers who receive the guide per quarter | drivers | 100 | 300 | 600 | My judgment: no driver-count data in this project; to be replaced by the company's own number. |
| Share of new drivers who use the guide in planning their shifts | % | 40 | 60 | 80 | My judgment: onboarding material is read by many but applied by fewer. |
| Increase in the share of a new driver's working hours that fall on weekend nights | percentage points | 0 | 2 | 5 | My judgment. The effect on driver behaviour is unknown; the low value is 0 on purpose. |

### Success metric (KPI)
Share of working hours on weekend nights for the new-driver group compared with the previous new-driver group, with trips per driver-hour in those hours not lower than the previous group. The rule is set before the guide goes out: success if the share rises by at least 2 percentage points and trips per driver-hour does not fall; stop or change the guide if the trips per driver-hour falls.

### Risks and trade-offs
- If the night trip counts show that weekend nights are not busier in absolute terms, the guide has no basis and should not go out.
- More new drivers on weekend nights can lead to oversupply in those hours.
- Night driving has fatigue and safety costs that this analysis does not measure.
- Day-level shares are not independent (weekly rhythm), and the weekday-spread yardstick is a custom threshold (see the 07 amendment).
- The timestamp time zone was assumed to be New York local time and was not verified.

## R3

### Recommendation
Do not base a decision to enter new zones on the congestion-pricing result in I4. First run a follow-up analysis: add 2025 data to place the change in time, compare trip counts and not only shares, add a comparison group of trips with neither end inside the zone, repeat the comparison with other year pairs as a placebo, and check that the `request_source` column added to yellow files in 2026-06 to 2026-09 does not change coverage. Decide on entry only after this.

### Owner (department)
Business development (entry decision), with the analytics team (follow-up).

### Rationale
Based on I4. The share of trips touching the congestion zone fell more than the 2023-2024 change for both services, but the 08 critique found that the evidence cannot separate a fee effect from trend, season or data change: one baseline year pair, a HVFHV baseline already falling (-1.69 pp), a yellow effect that is gone in June-September, 2025 missing, and an unexplained schema change in the same months as the yellow rebound. The "no new hotspot" statement rests on top-15 single-zone changes without a noise reference. A recommendation to enter or avoid a zone would go beyond the evidence, so the recommendation is to fill the gaps first.

### My assumptions and values

| Assumption | Unit | Low | Base | High | Basis |
|---|---|---|---|---|---|
| Analyst effort for the follow-up | person-days | 5 | 10 | 20 | My judgment: 24 more monthly files (2025, both services) and four extra checks. |
| Delay of the entry decision while the follow-up runs | weeks | 2 | 4 | 8 | My judgment. |

### Success metric (KPI)
A written go or no-go on zone entry, made with a rule fixed before the follow-up results: an outside zone is a candidate only if its 2024-2026 share gain is positive, larger than its own 2023-2024 change, and its 95% interval excludes 0. Success is that the decision is made within the delay above, using this rule.

### Risks and trade-offs
- The wait may let a competitor enter first.
- The 2025 data may show that the change began before the fee, which would weaken the fee story and the case for entry.
- Trip counts may show that trips inside the zone did not fall at all, and the share changed only because outside trips grew.
- Zone ID meaning across years and the time zone are still unverified.
