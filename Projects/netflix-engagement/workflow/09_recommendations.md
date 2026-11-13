Author: human
Status: final
<!-- 한국어 힌트: 둘째 줄은 항상 Status 줄이다. 허용 값은 draft(작성 중) 또는 final(완료). 반론에 답한 뒤 final로 바꾼다. -->

# 09 Recommendations

## R1

### Recommendation
When planning future H2 release and licensing slates, do not tilt the genre mix by earlier H1-to-H2 shifts. Use the most recent half-year genre mix (H1 2026) as the planning baseline, treat it as provisional, and score it against the H2 2026 result when Netflix's first annual engagement report is published.

### Owner (department)
Content planning and release scheduling (the decision owner named in 02).

### Rationale
- Based on I1: no genre passes my pre-set seasonal rule in seven half-years; check 1 alone already fails (best margin 0.49 pp against a 2 pp threshold). My 02 decision rule then says to keep the latest half-year mix as the baseline. I2 is a single observation and is not used as a reason.
- Answers to 08_critique (what changed):
  1. Low power of the rule: accepted. 2 pp was chosen as roughly twice the effect of the largest single title (about 0.9 pp), a noise-scale argument, not a business one. I did not test whether the rule detects a planted pattern. 07 now says so. This does not change the recommendation, which is the cautious default, not a seasonal tilt.
  2. Coarse genre groups: accepted as a limit; no alternative mapping was run.
  3. I2 causal claim: accepted; I2 is narrowed to one observation.
  4. Check 2 is circular: accepted as a limit.
  5. Noisy "new" stratum: partly rejected. Check 1 alone fails at all three thresholds, so that stratum does not decide the result.
  6. Sci-Fi & Fantasy average-based lead (1.85 pp, [0.33, 3.46]): accepted; added to 07 as a weak lead. It rests on one jump and is not a pass under the rule I fixed in advance.
  7. "Independent recomputation" wording: accepted; changed in 07.
  8. Advice beyond the data: partly accepted. The baseline is not tested and is exposed to big titles, so it is marked provisional and tied to a scoring plan below.
  9. Coverage and scope: noted as limits.
- Impact modelling (step 10) is skipped: there is no validated seasonal effect to model.
- Not done: a power test with a planted pattern, an alternative genre mapping, a per-half scope, hand checks of the ambiguous matches.

### My assumptions and values
No quantified assumptions. Impact modelling was skipped because no validated effect exists.

| Assumption | Unit | Low | Base | High | Basis |
|---|---|---|---|---|---|
| (none) |  |  |  |  | No validated seasonal effect to size |

### Success metric (KPI)
Prediction written on 2026-11-12: for each tested genre group, the H2 2026 share equals the H1 2026 share within 2 pp (same mapping and scope rules). Scoring: when the first annual report is published (expected Q1 2027), derive H2 2026 hours by title if the report allows it, and compute the absolute difference per genre group. Success = all tested groups within 2 pp; partial = some groups outside, which I report as the groups that moved. If H2 2026 cannot be derived from the annual report, the KPI is not scorable; I state this in advance.

### Risks and trade-offs
- The baseline ignores known upcoming releases, so a planner may miss a real seasonal effect that my rule could not detect.
- H1 2026 is the half with the highest unlabelled share (4.49%) and can be moved by its own big titles.
- Coarse genre groups may hide movements inside large groups; a different mapping could change the result.
- The KPI can fail simply because the 2026 slate differs, not because the baseline idea is wrong.

*Writing note: this draft was prepared by Claude in chat, following my pre-set decision rule and the 08 critique; I reviewed it before committing.*