Author: ai/impact-modeler

# 10 Impact forecast (nyc-congestion-pricing)

Inputs read: `09_recommendations.md`, `05_analysis.md`, `06_validation.md`, `08_critique.md`. Code: `pipeline/impact_model.py`; output and evidence: `outputs/impact_model.log`, `outputs/impact_results.json`. Machine-readable assumptions: `workflow/10_impact_assumptions.json`. No data files were opened.

## 0. What this forecast is, and its limits

- The project has no driver-level data, no earnings, no waiting times, no fares (05, 08). So no effect of any recommendation can be estimated from data. The scenario values for effects are the human's judgment (09). My part is to turn them into forecasts, power calculations and sensitivity.
- All results are in relative terms (percent, percentage points, driver counts). There is no baseline trips per driver-hour in the project, so I do not convert to trips or money. To convert: incremental trips per driver-hour = baseline x the percent in this file.
- Four values are modeler placeholders (marked `modeler_placeholder` in the JSON, a type outside human/data/benchmark; I used it because inventing a benchmark source would be false): the two noise levels of trips per driver-hour (R1), the spread of weekend-night hour share across drivers (R2), and the test settings (alpha 0.05, power 0.80). They are unsourced. The sample sizes below depend on them; the human should replace them with fleet numbers.
- No external benchmark is used. No web source was consulted.
- Numbers excluded: none FAIL. One PASS number was not used on purpose: the Jaccard stability of the 17-zone list (0.889-1.000), because 08 shows it is in-sample (each month is compared with a full-period list that contains it), so it is not a valid input for how stable a list will be in a pilot.

## 1. Assumptions table

| ID | Assumption | Low | Base | High | Unit | Source | Type |
|---|---|---|---|---|---|---|---|
| R1.n | Drivers per group | 20 | 50 | 100 | drivers | 09 R1 | human |
| R1.follow | Share who follow the list | 30 | 50 | 70 | % | 09 R1 | human |
| R1.effect | Change in trips per driver-hour among followers | 0 | 3 | 8 | % | 09 R1 | human |
| R1.weeks | Pilot length | 8 | 8 | 12 | weeks | 09 R1 | human |
| R1.list_coverage | Yellow pickups covered by the 17-zone list | 50 | 50 | 50 | % | 05 s3, 06 Q1 PASS | data |
| R1.sigma_b | Between-driver SD of mean trips per driver-hour | 0.15 | 0.20 | 0.30 | fraction of mean | placeholder | modeler placeholder |
| R1.sigma_w | Week-to-week SD within a driver | 0.30 | 0.40 | 0.50 | fraction of mean | placeholder | modeler placeholder |
| R2.N | New drivers per quarter | 100 | 300 | 600 | drivers | 09 R2 | human |
| R2.use | Share who use the guide | 40 | 60 | 80 | % | 09 R2 | human |
| R2.pp | Rise in share of hours on weekend nights | 0 | 2 | 5 | pp | 09 R2 | human |
| R2.night shares | Weekday vs weekend night share (yellow 13.0-15.9 vs 25.6-29.3; HVFHV 16.2-18.5 vs 26.3-28.5) | see JSON | midpoints | see JSON | % of day's trips | 05 s5, 06 Q3 PASS | data |
| R2.sd_share | SD across drivers of weekend-night hour share | 5 | 8 | 12 | pp | placeholder | modeler placeholder |
| R3.days | Analyst effort | 5 | 10 | 20 | person-days | 09 R3 | human |
| R3.delay | Decision delay | 2 | 4 | 8 | weeks | 09 R3 | human |
| R3.k | Drift-years assumed to continue 2024 to 2026 | 2.0 | 1.5 | 1.0 | years | my scenario on 05 s6 numbers (PASS, 06 Q4) | data (scenario) |

Interpretation point for the human on R2.pp: the table does not say whether the 0/2/5 pp applies to users of the guide only or to the whole new-driver group. I modeled both (reading A: users only, group shift = use x pp; reading B: whole group). The answer changes the verdict (section 3).

## 2. R1: yellow pickup-zone list pilot

Label: **causal design, assumption-based estimate.** With random assignment to the pilot and comparison groups, the difference in trips per driver-hour is a causal effect of offering the list. The size of the effect is not estimated from any data; it is the human's assumption. The coverage figure (50% of pickups) is descriptive, not causal.

Effect on the pilot group as a whole (intention-to-treat) = follow share x effect among followers, because non-followers are in the pilot group and dilute the difference.

| Scenario | Drivers/group | Follow | Effect (followers) | Weeks | Estimated ITT effect | Standard error | Smallest effect the pilot can detect (80% power) | Chance the 09 success rule is met* |
|---|---|---|---|---|---|---|---|---|
| Low | 20 | 30% | 0% | 8 | 0.0% | 5.8% | 16.2% | about 2.5% (false-positive level) |
| Base | 50 | 50% | 3% | 8 | 1.5% | 3.7% | 10.2% | about 6% |
| High | 100 | 70% | 8% | 12 | 5.6% | 2.2% | 6.1% | about 74% |

*Rule in 09: difference at least +3% and the 95% interval above 0. Computed with a normal approximation; a simulation of the same noise model (4,000 runs each, `outputs/impact_model.log`) gives 3.0%, 6.2%, 73.7%, so the formula is consistent. The low scenario's 2.5% is the chance of a false success when the true effect is 0.

Findings, under these assumptions:
1. The base scenario's ITT effect (1.5%) is below the pre-set success line (+3%). Even if the effect exists as assumed, the 09 rule would be met in about 6% of pilots. The +3% line is only reached on average if (follow share) x (effect) is at least 3%: for example 100% compliance at 3%, or 37.5% compliance at 8%.
2. A pilot of 20-100 drivers per group can only detect an ITT difference of about 6% to 16% (8-12 weeks). The base case's smallest detectable difference is 10.2%, which is about 7 times the base effect. A "no difference" result would therefore not show that the list does not work.
3. Estimated drivers per group needed to detect +3% (80% power, alpha 0.05 two-sided, base noise): 581 for 8 weeks, 407 for 12 weeks. To detect the base ITT of 1.5%: 2,326 (8 weeks), 1,628 (12 weeks). To detect the high ITT of 5.6%: 167 (8 weeks), 117 (12 weeks).
4. Range of the business effect: roughly 0% to 5.6% more trips per driver-hour for the pilot group, base 1.5% (relative to its baseline). This range is wholly from the human's inputs. Oversupply (09 risk) would lower it; it is not modeled because there is no supply data.

Sensitivity ranking for P(success), one parameter at a time from the base, others fixed (swing = difference between P(success) at the parameter's low and high):

| Rank | Parameter | Low to high | P(success) low / high | Swing |
|---|---|---|---|---|
| 1 | Effect among followers | 0 to 8% | 2.5% / 19.4% | 16.9 pts |
| 2 | Follow share | 30 to 70% | 4.3% / 8.3% | 4.0 pts |
| 3 | Drivers per group | 20 to 100 | 4.5% / 8.4% | 3.9 pts |
| 4 | Weekly noise (placeholder) | 0.30 to 0.50 | 7.6% / 5.3% | 2.4 pts (higher noise lowers it) |
| 5 | Pilot weeks | 8 to 12 | 6.1% / 7.1% | 1.0 pts |
| 6 | Between-driver noise (placeholder) | 0.15 to 0.30 | 6.3% / 5.9% | 0.4 pts |

The unknown effect size dominates; group size, which the human can choose, comes third. Extra weeks help little because the ANCOVA design (pre-period baseline per driver) already removes most between-driver variation, under my placeholder noise levels.

### Experiment design R1
- Metric: trips per driver-hour, pilot minus comparison group, relative. Second: share of the drivers' pickups inside the list zones. Note for the second metric: the 17 list zones already hold 50% of yellow pickups by construction (05), so a typical driver's baseline share may already be near 50%; the room to rise is limited and the baseline for the comparison group should be measured first.
- Design: random assignment of drivers; a pre-period of the same length as the pilot for each driver, used as a covariate (ANCOVA); estimate the difference with its 95% interval.
- Minimum detectable effect: the business case needs +3% for the group as a whole. Calculation (placeholders sigma_b 0.20, sigma_w 0.40): total variance of a driver's 8-week mean = 0.20^2 + 0.40^2/8 = 0.060; correlation with pre-period mean = 0.04/0.06 = 0.667; residual SD = sqrt(0.060 x (1 - 0.667^2)) = 0.1826. n per group = 2 x ((1.96 + 0.8416) x 0.1826 / 0.03)^2 = 2 x 17.05^2 = about 581. With 12 weeks the residual SD is 0.1528 and n = 407.
- Required sample size: about 410 to 580 drivers per group for +3% (range under the noise assumptions is wider; rerun `impact_model.py` with the fleet's numbers). The human's 50 per group cannot reach it. Options: a larger pilot, a lower bar stated in advance (an ITT of 10% is the base MDE at 50 per group, not realistic), or treat the 50-driver pilot as a feasibility study (follow rate, data collection, zone-level oversupply signs) and not as a test of the effect.
- Duration: 8 to 12 weeks of pilot plus an equal pre-period; at least one pass through the two seasonal zones if possible (the list was made from one year of data).
- Guardrails: earnings per hour (fares are not in the project), pickups per driver in list zones (oversupply), hours worked per driver (so that the effect is not from changed hours), contamination between groups (drivers sharing the list), and a stop rule if the pilot group's trips per driver-hour falls.
- Also note the 09 rule treats the interval as one-sided at 0; my calculation uses a two-sided 95% interval, which is slightly more demanding.

## 3. R2: new-driver weekend-night guide

Label: **correlational basis, assumption-based behaviour effect.** The finding behind the guide (weekend days have a larger night share, 25.6-29.3% vs 13.0-15.9% for yellow, 26.3-28.5% vs 16.2-18.5% for HVFHV, 12 of 12 months under the primary definition) is a descriptive pattern in aggregate trips. It is not causal evidence that drivers earn more at night on weekends. Any effect of the guide on shifts or on trips per driver-hour would be causal only if measured in a randomized comparison. 08 also notes that the headline gap depends on the S3 reading (pooled 13.12 vs 4.57 pp for yellow), so the basis is weaker than "12 of 12" suggests.

Step 0 check implied by 09 (share vs count). From the PASS share ranges only, I can compute the break-even: weekend nights hold more trips per day than weekday nights unless a weekend day's total volume is below this fraction of a weekday's total volume: yellow 0.44 (best) / 0.53 (mid) / 0.62 (worst case); HVFHV 0.57 / 0.63 / 0.70. The actual volume ratio is not in my input files, so this does not settle 08's point. It shows what the human's first step must compare: weekend daily volume would need to be less than about 53-62% of weekday volume (yellow) or 63-70% (HVFHV) for the share gap to be a denominator effect. That is a threshold from my arithmetic on monthly ranges (it mixes months at the extremes), not a data result.

Scenarios (drivers per quarter):

| Scenario | New drivers | Use share | Shift in weekend-night hours (users) | Users of guide | Group shift, reading A (users only) | Group shift, reading B (whole cohort) |
|---|---|---|---|---|---|---|
| Low | 100 | 40% | 0 pp | 40 | 0.0 pp | 0.0 pp |
| Base | 300 | 60% | 2 pp | 180 | 1.2 pp | 2.0 pp |
| High | 600 | 80% | 5 pp | 480 | 4.0 pp | 5.0 pp |

Findings:
1. The 09 success line is a rise of at least 2 pp in the cohort's weekend-night share. Under reading A the base (1.2 pp) is below the line and only the high scenario (4.0 pp) is above it. Under reading B the base is exactly on the line (2.0 pp) and the low scenario is 0. The human should say which reading is meant.
2. Range for the group shift: 0 to 4.0 pp (reading A) or 0 to 5.0 pp (reading B). No effect on trips per driver-hour is forecast; the human's table gives none, and the data have no per-driver outcome.
3. Sensitivity (reading A, others at base; group shift in pp): shift among users 0 to 3.0 (largest), use share 0.8 to 1.6, new drivers per quarter does not change the average shift; it changes the statistical power and the total hours moved. Ranking: 1 shift among users, 2 use share, 3 cohort size (affects power, not the average).

### Experiment design R2
- Metric: share of each new driver's working hours on weekend nights (Fri/Sat nights, same night definition as 07, to be fixed before the start); guardrail trips per driver-hour in those hours, not lower than the comparison group.
- Design comparison. The 09 plan compares a new cohort with the previous cohort. That is simple but confounded by season, hiring mix and market change (correlational). A random split of each cohort into guide and no-guide is causal but halves the sample.
- Minimum detectable effect and sample size (80% power, alpha 0.05 two-sided; SD of the share across drivers is a placeholder, base 8 pp): n per arm = 2 x ((1.96 + 0.8416) x 8 / delta)^2. For delta = 2 pp: 251 per arm (98 if SD is 5 pp; 565 if 12 pp). For delta = 1.2 pp (the base group shift under reading A): 698 per arm (273 to 1,570). For delta = 5 pp: 40 per arm.
- With the base 300 new drivers per quarter: random split (150 per arm) can detect about 2.6 pp; cohort-versus-previous-cohort (300 vs 300) about 1.8 pp (but not causal). With 100 per quarter the figures are 4.5 and 3.2 pp; with 600, 1.8 and 1.3 pp. So one quarter at base size can only just detect the 2 pp line; pooling two quarters or the high cohort size would be better.
- Duration: one onboarding quarter to assign, then at least 8 weeks of working hours per driver; two quarters if the cohort is small.
- Guardrails: trips per driver-hour on weekend nights (oversupply), total hours per driver and night hours per driver (fatigue and safety proxy; not in this project's data), driver drop-out in the first months. Do not send the guide if the Step 0 count check shows weekend nights are not busier in absolute trips (09 already says this).

## 4. R3: follow-up before zone entry

Label: **correlational.** The follow-up compares before and after shares and cannot, by design, prove a fee effect. R3 itself has no benefit to forecast in trips or money; it is a cost and timing decision.

- Cost and delay (human's range): 5 / 10 / 20 person-days and 2 / 4 / 8 weeks (low / base / high). No cost per person-day or competitor-entry risk is given, so I give no money figure. These two are not linked by any data; the ratio at base is 10 person-days over 4 weeks.
- What the follow-up could show. The 05 test compares the 2024 to 2026 change (two years) with the 2023 to 2024 change (one year). A scenario I add: if the earlier drift continued at the same yearly pace for k years, the unexplained part of the change is Delta_main - k x Delta_drift. Numbers are from the PASS values in 05 s6 (06 Q4). Approximate 95% intervals combine the two reported intervals assuming independence (an approximation of mine; the real follow-up should bootstrap it).

| Service | Delta_main | Delta_drift | k = 1 (as in 05) | k = 1.5 | k = 2 (linear trend) |
|---|---|---|---|---|---|
| Yellow (pp) | -1.99 | -0.18 | -1.81 [-2.74, -0.88] | -1.72 [-2.81, -0.63] | -1.63 [-2.92, -0.34] |
| HVFHV (pp) | -4.26 | -1.69 | -2.57 [-3.29, -1.85] | -1.72 [-2.63, -0.82] | -0.88 [-2.00, +0.24] |

Reading: under a linear-trend baseline, the HVFHV change that remains after removing the trend falls from -2.57 pp to -0.88 pp and its interval includes 0. The yellow result is less sensitive (still below 0), but 06 F3 shows its Jun-Sep margin is about zero (-0.40 vs drift -0.34 pp), so the yellow all-month figure hides two regimes. Under these assumptions the existing evidence for a break at the fee date is fragile for HVFHV, which supports waiting for the 2025 data. This does not show that the fee had no effect.
- Estimated range of outcomes of the follow-up (qualitative, from the scenario): it could weaken the HVFHV case (k near 2), leave a yellow shift that is concentrated in Jan-May, or show a break before the policy date. The probabilities of these are unknown; I give none.
- Sensitivity: cost scales linearly with person-days (5 to 20: a factor of 4). Delay is the larger business risk (competitor entry), and the model cannot rank it because no value is given for a week of delay. Largest uncertainty in the evidence: k (the baseline assumption), which moves the HVFHV residual from -2.57 to -0.88 pp.
- Experiment design: no randomized experiment is possible. Pre-set tests: (a) 2025 monthly series to locate the break (the policy start date is not in my inputs and I did not verify it); (b) placebo year pairs and the same margin calculation, for the distribution of margins without a policy; (c) counts of trips with neither end in the zone as a comparison group; (d) check that `request_source` does not change yellow coverage. Metric: the margin Delta_main - k x Delta_drift and its 95% interval. The human's entry rule (positive gain, larger than own 2023-2024 change, 95% interval excluding 0) works as the decision rule; I did not compute its power because zone-level counts are not in my inputs. Guardrail: report counts as well as shares.

## 5. Caveats

- Effect sizes (R1 effect, R2 shift) are judgment, not data; the forecasts are only as good as these inputs. The low value 0 is kept on purpose in both.
- The noise levels are unsourced placeholders. If real driver-level variation is larger, the required samples grow with the square of the noise (1.5 times the noise = 2.25 times the sample).
- The R1 model assumes random assignment, no contamination, a fixed follow share, equal-length pre-period, normally distributed means and no oversupply feedback. Contamination (09 risk) pulls the measured difference toward 0.
- Trips per driver-hour is not earnings (09 risk); I do not model fares.
- Inputs inherit 08's objections: the list's stability evidence is in-sample (not used here), "workable" has never been measured, the night gap depends on the S3 reading, time zone and zone-ID meaning are unverified (06).
- The R3 trend scenario assumes a linear drift and independent CIs; one earlier year pair is a weak baseline (06 F3).
- No guarantee is implied: all outputs are estimates under these assumptions.

## 6. Questions for the human

1. R1: do you accept that the base case (1.5% ITT) is below your +3% rule? Raise the sample, lower the rule, or reframe the pilot as feasibility.
2. R2: does the 0/2/5 pp apply to users only or to the whole cohort?
3. Replace the four placeholders (noise, share SD) with fleet data if available.
