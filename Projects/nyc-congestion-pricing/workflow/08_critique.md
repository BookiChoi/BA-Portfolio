Author: ai/critic

# 08 Critique of 07_insights.md (nyc-congestion-pricing)

Inputs read: `07_insights.md`, `05_analysis.md`, `06_validation.md`. No new numbers are created; each number quoted below is tagged with its source (05 = analysis, 06 = validation, 07 = insights).

Status of validation: 06 gives overall PASS with 775 checks and 0 mismatches. No insight rests on a number that FAILED validation. That is a statement about reproducibility (the same counts come out of a second route). It says nothing about whether the metric measures what the insight claims. Most objections below are about that gap. The validator also did not check the timestamp time zone, zone-ID meaning across 2023-2026, or the PNG charts (06, section 5; 07, Notes).

---

## I1: yellow zone list works, HVFHV list does not

**Alternative explanations**
- The yellow vs HVFHV gap in n80 (36 vs 128; 05, section 3) may come from how each service works rather than from demand "spread". Yellow trips are mostly street hail and are concentrated by where passengers can hail. HVFHV trips are app-dispatched over a wider area. The data shows pickups happened. It does not show where unmet demand is.
- Pickups are realized outcomes that depend on where drivers already position themselves. A concentrated pickup map can be the result of existing cruising habits. It does not show that a list would add value.

**Confounders and measurement**
- The stability evidence is mislabelled and partly circular. 07 calls the Jaccard "month-to-month overlap". 05, section 3 defines it as each month's list compared with the full-period list, and that full-period list contains the month being tested. The overlap is therefore in-sample and biased upward. A fair test would build the list on earlier months and test it on later months. 06 recomputed the number (0.963 and 0.940) but did not change the definition.
- The two guidance lists use different targets, 50% for yellow and 40% for HVFHV (05, section 3). The sizes (17 vs 43 zones) cannot be compared as "workable vs not workable". The 07 reasoning that a 50% HVFHV list would need "more than 30 zones" is the rule's threshold, not evidence of failure.
- 05 notes that pickup counts favour large zones. HVFHV covers outer-borough zones that differ in size from Manhattan zones. Counting zones is not counting area or street distance.

**Data limitations**
- 12 months (Oct 2025 - Sep 2026), one year, and the seasonal flags rest on 12 observations per zone. n50/n80 CIs are integer and can be zero width ([36, 36] for yellow n80; 05, section 3), which understates uncertainty about the structure.
- No earnings, waiting time, or supply data (07 admits this). "Workable" is never defined or measured.

**What would overturn it**
- A list built on the first 6 months that fails to cover about half of trips in the last 6 months (a time-split test). A comparison of coverage per unit of area or per driver-hour.

**Beyond the evidence**
- "Workable" and "does not need frequent updates" go beyond a coverage count. "Too many zones for a list to work well" for HVFHV is a conclusion about driver benefit that was not tested.

---

## I2: airport destination guide supported only for HVFHV at JFK and LaGuardia

**Alternative explanations**
- The "more concentrated than average" verdict depends on the benchmark. The benchmark is the share of the top 5 overall pickup zones (yellow 19.64%, HVFHV 7.17%; 05, section 4). That is a pickup distribution compared with a destination distribution. HVFHV has a very low baseline because its pickups are spread over many zones (see I1). So almost any Midtown-directed airport flow exceeds 7.17%. The cross-service contrast ("only HVFHV") may be partly an artifact of the low HVFHV baseline and not a difference in airport behaviour. A same-service benchmark of overall destination concentration was not used.
- Passenger mix (visitors vs residents) and the fare structure differ between services. That could explain the destination differences with no link to guidance value.

**Confounders and selection**
- Same-airport destinations are kept (05, section 4: 90,980 yellow JFK, 72,235 HVFHV JFK, with JFK itself in the top 5 of both). Those trips fill one of the five slots. For yellow JFK the top-5 share (16.22%) includes JFK itself as the first destination. For HVFHV JFK, JFK itself is rank 2. The delta is partly "trips returning to the same airport", which is not "where passengers go". The plan chose this, but 07 gives the result at face value.
- Invalid destinations (IDs 264/265) are excluded: 813,005 HVFHV JFK trips and 659,634 LaGuardia trips (05, section 4; about 20% and 13% of pickups per 07). If these trips (unknown or outside NYC) differ from the rest, the shares and the verdict could move. The denominator is only valid-destination trips, so the top-5 share is calculated on a selected 80-87% of the trips. 06 only verified the counts (F6).
- HVFHV airport results are reported with exclusions this large, while yellow exclusions are 88,951 of about 1.9 million at JFK. The exclusion rates differ by service and affect the service comparison.

**Data limitations**
- Destination is where the passenger goes, not a driver return trip or a next fare (05 limitation). HVFHV Newark has 11 valid trips and yellow Newark is driven by Newark-to-Newark trips, so only two airports are really tested per service. The decision uses a point-estimate rule. The yellow LaGuardia difference (-1.06 pp [-1.72, -0.44]; 05) is small, so "do not name" vs "name" for that pair is a threshold call.
- The out-of-sample check by 06 (odd vs even weeks) only tests selection bias of the top 5. It does not test benchmark choice, the same-airport trips, or the unknown destinations.

**What would overturn it**
- Recompute with same-airport trips removed and with a destination-based baseline. Run a sensitivity that assigns the 264/265 trips to the worst and best cases (all in one zone vs spread evenly), which would show whether the result is robust to 13-20% missing destinations.

**Beyond the evidence**
- "Supports a 'where airport passengers go' guide" is a business conclusion. The data shows only that 5 destinations hold 12-16% of trips, which 07 itself says is a minority. The claim "the rule does not support yellow" is correct as a rule result, but the yellow LGA share (18.58%) is close to the baseline of 19.64%.

---

## I3: night share larger on weekend days, in every month, both services

**Alternative explanations**
- The statistic is a share of the day's trips. A larger weekend night share can come from fewer daytime trips (weekday commuting volume in the denominator), not from more night trips. 07 words this correctly as share, but the interpretation ("separate night guidance") treats it as night demand being greater. No counts of night trips per day are shown.
- Day boundary: "night" is 22:00-04:59 of the pickup date, so a weekend date includes early-morning trips from the previous evening plus its own late evening. The result depends on which night is assigned to which day. This is exactly the S3 issue below.

**Confounders and measurement**
- Researcher choice after seeing results. The plan's S3 wording was ambiguous. The human chose the "intent" reading in `05a_human_review.md` after 05 showed both. Under the literal reading, gap > spread passes in only 4 of 12 months for yellow and 9 for HVFHV, and the pooled effect is 4.57 pp yellow and 3.97 pp HVFHV (05, section 5), against 13.12 and 10.16 in the primary variant. The chosen reading is the one that gives the stronger result. The choice may be defensible, but the headline magnitude (about 10-13 pp) is sensitive to it by a factor of about three. 07 mentions this but the Claim does not.
- Internal inconsistency. The Claim says "in every one of the 12 months, for both services". The reading the human chose for S3 gives 11 of 12 for HVFHV (December 2025: gap 7.25 pp vs spread 8.30 pp; 05, section 5), and 07 itself says so. The 12 of 12 holds only for the primary variant. The Claim should not be stronger than the evidence under the chosen reading.
- The yardstick is arbitrary. The spread is the widest difference among Mon-Thu pooled shares over 3-5 days per cell (05). The weekday group includes Friday, which the spread leaves out. Beating a Mon-Thu spread is a custom threshold. 05 notes that this spread is biased upward (so the test is demanding), but it also ignores holidays, events and weather days that would make weekday spread larger in reality.
- Timestamps are assumed to be New York local time (05, Step 1; 06, "Not verified"). If a month or file uses a different convention, the 22:00-04:59 window would shift. The check was not done by anyone.
- Hedges g of 2.75-7.88 and p-values at the floor show that day-level shares are nearly deterministic by day type. Treating days as independent overstates precision (weekly rhythm; 05 limitation). The Mann-Whitney agreement (24 of 24; 06) does not fix dependence, because it is also a test on independent observations.
- The bootstrap unit differs from the plan (DOW cells, not day type; F4). 06 did not test a day-type-only bootstrap, so the CIs for the weakest month (yellow margin 4.27 pp [1.78, 6.09]) rest on a different design than the one approved.

**Data limitations**
- One year only. December 2025 is the weakest month, and holidays (11 excluded dates) and DST days (kept on wall-clock hours) touch this month and others. Only 12 months, with 3-5 days per cell.

**What would overturn it**
- Show night trip counts per day by day type: if weekend nights are not higher in absolute counts, the share finding is a denominator effect. Verify time zone on a known event (for example, a fixed-hour pattern). Run the day-type-only bootstrap and a block bootstrap by week.

**Beyond the evidence**
- "Supports separate night guidance" is not shown by a share difference. 07 correctly says it does not know whether drivers already know this. The Claim "much larger share" is true for the primary variant but understated in its sensitivity to the S3 choice.

---

## I4: share of trips touching the congestion zone fell after pricing

**Alternative explanations**
- Pre-existing and unrelated trends. HVFHV share was already falling (-1.69 pp for 2023-2024; 05, section 6) and the yellow drift is -0.18 pp [-0.70, 0.33]. The test "abs(main) - abs(drift)" implicitly assumes the HVFHV drift would stop or stay at one-year size. If the decline continues at the earlier pace, the margin is not a fee effect. A single year pair is a weak baseline (05 and 06 F3 both say so).
- Timing contradicts a simple fee story for yellow. The drop is concentrated in Jan-May 2026. In Jun-Sep, 2026 vs 2024 is -0.40 pp against a drift of -0.34 pp (06, F3), so the margin is about zero, and monthly yellow shares in Jul-Aug 2026 (74.9%, 74.7%) are near 2024 (75.0%, 74.4%; 05). If a fee in force all year caused the drop, why did yellow recover to its 2024 level? A seasonal, demand or data explanation fits the pattern at least as well. The headline "about 2 pp" averages two different regimes.
- Jan-Sep 2025 is not in the comparison (05 uses 2023, 2024, 2026), so the timing relative to the policy start cannot be examined. The three-year design cannot say when the change began.
- Composition changes in the data. The yellow files for 2026-06..09 gain a `request_source` column (05, Step 1), and yellow volume in Oct-Dec 2025 is above the sample range (05 flag). The yellow rebound begins in the same months. This does not prove a reporting change, but nobody has ruled it out.
- Other shifts: rider mix, work-from-home, fares, trip length, weekday mix and the leap day (05 limitations: "not controlled", "weekday mix not corrected").

**Confounders and measurement**
- The measure is a share, so a fall can come from growth of outside-zone trips with inside-zone trips flat, or from the opposite. 07 notes "shares, not trip counts" but still words the result as "fell". The mechanism (fewer trips in the zone or more trips elsewhere) is unknown.
- HVFHV excluded trips (invalid ID at either end) rise: 4.07%, 4.12%, 4.50% (05, section 6). If excluded trips are not random with respect to the zone, this is a moving selection filter. S4 (all trips as denominator) keeps the decision, which helps, but S4 mixes in the invalid trips as "not touching the zone".
- Zone ID meaning across years is unverified (05, 06). The 38-zone list is "as given" and zones do not match the legal boundary. Six neighbouring zones only, because none across the rivers touches the list (05, Step 2); the "displacement" test therefore cannot see displacement across rivers.
- The displacement claim is weak. Showing that the top 15 single-zone gains are small (+0.21 pp, +0.12 pp) says nothing about diffuse redistribution across about 225 outside zones, and zone-level changes have no noise reference (no CI, no drift comparison at zone level). The largest yellow changes are losses outside the list: JFK (-0.94 pp) and LaGuardia (-0.69 pp; 05, section 6). So yellow's outside-zone change is not a simple "inside to outside" move, and it hints at changes that are unrelated to the CRZ.
- Week-block bootstrap treats the 40 weeks per period as exchangeable and periods as independent. Seasonality and trend within a year are not modelled. The p-values are at the floor (0.0005), so they carry no information; only the CIs do.

**Data limitations**
- Three years of Jan-Sep only; no October-December comparison; one baseline year pair; leave-one-month-out keeps the rule (06: yellow +1.47 to +2.13 pp, HVFHV +2.40 to +2.70 pp), but that checks months, not the baseline design.
- Duplicates kept (1.14% of yellow rows; 06 F1); the yellow margin moves from +1.81 to +1.89 pp, small.

**What would overturn it**
- A placebo with other year pairs (for example 2022 vs 2023 if data are available) to see how often a margin of +1.81 / +2.57 pp appears without a policy. Inclusion of 2025 to place the break in time. Trip counts by zone group, not shares. A comparison group unlikely to be affected (for example trips with neither end inside the zone, in absolute counts). A check that `request_source` or other schema changes do not alter yellow coverage.

**Beyond the evidence**
- 07 states "This does not show that the fee caused it", which is good. But the phrase "after congestion pricing ... fell ... more than the 2023-2024 change" and the decision label "real shift" imply a policy link. "Did not move to one place" is an absence-of-evidence claim based on top-15 lists with no noise benchmark. The word "no obvious new hotspot" is therefore weaker than the Claim sentence suggests.

---

## Cross-cutting issues
- Time zone and zone-ID meaning are unverified, and charts were not reviewed (06). They affect I3 (time zone) and I4 (zone IDs) directly.
- The 07 key-number reproduction covers only the Q1 yellow numbers (07, Notes). HVFHV, Q2, Q3 and Q4 numbers were not reproduced by the human; they rely on 06.
- Rule-based decisions ("name destinations", "real shift", "separate night guidance") are only as good as the plan's thresholds, which this critique did not review (02 and 04 were not in scope). Point-estimate rules can flip on small differences (see yellow LGA, I2).

## Ranked list of the strongest objections
1. I4: the before/after design has a single, non-flat baseline (HVFHV drift -1.69 pp), and the yellow effect disappears in Jun-Sep (06 F3). The data cannot separate a fee effect from trend, season, or data composition, and 2025 is missing.
2. I3: the headline gap depends on the S3 reading chosen after seeing results (pooled 13.12 vs 4.57 pp for yellow), and the Claim "12 of 12 for both" is not true under the chosen reading for HVFHV (11 of 12).
3. I2: the verdict depends on a mismatched benchmark (pickup top-5 share vs destination top-5 share) and on keeping same-airport trips and dropping 13-20% unknown destinations. The "only HVFHV" contrast may be a low-baseline artifact.
4. I1: the stability claim is in-sample (the full-period list includes the tested month) and mislabelled as month-to-month overlap; "workable" is never measured.
5. I3: share vs count. A higher weekend night share may reflect fewer daytime trips, not more night demand.
6. I4: the displacement conclusion ("no new hotspot") rests on top-15 single-zone changes with no noise benchmark and a neighbour set of only 6 zones; yellow airport losses (JFK, LaGuardia) show the shift is not a simple inside-to-outside move.
7. I3 and I4: unverified time-zone and zone-ID assumptions; Q3 bootstrap unit differs from the plan.
8. I1: coverage targets differ (50% vs 40%), so the list sizes are not comparable as "works vs does not work".
