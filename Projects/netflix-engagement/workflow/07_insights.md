Author: human
Status: final
<!-- 한국어 힌트: 둘째 줄은 항상 Status 줄이다. 허용 값은 draft(작성 중) 또는 final(완료). 핵심 숫자를 직접 재현한 뒤 final로 바꾼다. -->

# 07 Insights

## I1

### Claim
Under the rule I set before the analysis (a genre's share moves in the same alternating way between H1 and H2 by at least 2 percentage points (pp) in all six transitions, in every check), none of the tested genre groups passes in Netflix's seven half-year reports (H1 2023 to H1 2026). This is an absence of evidence under a strict rule and a coarse labelling, not proof that no seasonality exists. I did not test whether the rule would detect a seasonal pattern if one were planted.

### Evidence (numbers and where they are)
- Genres passing the rule: 0 at 2 pp, and also 0 at 1.5 pp and 3 pp (outputs/q1/genre_results.csv, chart3_check_matrix.csv; 06_validation.md: PASS, numbers recomputed by the validator).
- Check 1 alone already fails: the best margin is 0.49 pp (Sci-Fi & Fantasy), below all three thresholds. So the small "new" stratum, whose margin intervals are very wide, does not decide the result. Across all checks the best margin is -0.54 pp.
- Permutation check (check 1, all 5,040 orderings of the half-years): p = 0.138. At 2 pp no ordering passes and at 1.5 pp only 24 do (0.48%), so the rule is hard to pass even by chance (05_analysis.md, 06_validation.md: PASS). I do not use the all-checks p = 0.039 as evidence: its observed margin is negative, so it is not a pass.
- A weaker lead on an average basis: Sci-Fi & Fantasy's mean aligned shift in check 1 is 1.85 pp, bootstrap 95% interval [0.33, 3.46] (05_analysis.md). The interval resamples titles, not years, and rests on one large jump (+4.86 pp, H1 to H2 2025). I treat it as a lead to re-check, not a finding.
- Drama (average share 4.88%) was below the 5% cut-off; including it does not change the result (best margin -1.40 pp, 06_validation.md).

### Interpretation
For the content planner, this data does not support planning the H2 genre mix from earlier H1-to-H2 shifts. My 02 decision rule applies: use the latest half-year mix as the baseline. That baseline is provisional: no prediction test was run, and the latest half is exposed to its own big titles.
Limits: only seven half-years. Genre groups come from a fixed priority table that gives 57.0% of labelled hours a group different from the first IMDb genre; Drama is 4.88% while Crime & Thriller is 30.94%, so a large catch-all group may hide opposite movements. No alternative mapping was run. Matching was not checked by hand (725 ambiguous keys, 668 settled by "most votes", which favours popular works). Unlabelled hours rise from 3.08% to 4.49% of in-scope hours. Titles below Netflix's listing threshold are missing, and shares reflect what Netflix released and licensed, not only what viewers wanted.

## I2

### Claim
In one transition, the large Sci-Fi & Fantasy rise (+4.86 pp, H1 to H2 2025) coincides with very large viewing hours for two titles, Stranger Things and Wednesday. This is a single observation. I have not shown that big titles drive genre shifts in general.

### Evidence (numbers and where they are)
- The validator notes that this shift is mostly these two titles; no file gives their exact share of the shift (06_validation.md section 4).
- Check 2 (top 10 titles per half-year removed) moves the Sci-Fi & Fantasy margin from +0.49 to -0.54 pp, and both bootstrap intervals include zero ([-2.04, 1.12] and [-2.80, 0.22], 05_analysis.md). With the top 25 removed no genre comes close to 2 pp (06_validation.md note N4, an extra check outside the verdict).

### Interpretation
This is a hypothesis, not a result. Check 2 cannot tell "big titles add noise" apart from "big titles are scheduled in the same half each year". I did not test whether they are. I draw no business conclusion from it.

## Verification note
I did not reproduce the key numbers myself. I rely on the validator's recomputation (06_validation.md: PASS), which reused the analyst's cleaning, title-key and IMDb matching code; only the steps after the hours matrix are independent. A 400-key simple re-match agreed in 351 of 358 cases (98.0%), but it shares the "most votes" logic. The 30-row pilot match check was an AI first pass, not a hand check on IMDb. These are limits of this project.

*Writing note: this draft was prepared by Claude in chat from the validated results and my own conclusion ("nothing found"), and revised after the 08 critique; I reviewed it before committing.*