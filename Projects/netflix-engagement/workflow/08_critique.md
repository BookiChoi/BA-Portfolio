Author: ai/critic

# 08 Critique: Netflix engagement, Q1

Scope: I read `07_insights.md`, `05_analysis.md` and `06_validation.md` only. I ran no code and created no numbers. Every figure below is quoted with its source. Statements marked "(my inference)" are reasoning, not data. No insight has a number that FAILED validation: the overall verdict in `06_validation.md` is PASS. That verdict covers recomputation of the numbers, not the interpretation the insights build on them.

## I1: "No genre shows a seasonal pattern under the pre-set rule"

### 1. Alternative explanations
- The null result may come from the rule, not the data. `06_validation.md` section 4 says 0 of 5,040 orderings of the seven shares pass at 2 pp, so "a pass would have been rare even by chance". `05_analysis.md` (permutation section) says 24 orderings (0.48%) pass at 1.5 pp, and none at 2 or 3 pp. A rule that almost nothing can pass, even under random reordering, has very little power. The non-finding then says little about whether seasonality exists. The insight does say "absence of evidence", but the rule's near-zero pass rate is not named as the reason the evidence is weak.
- A real but small seasonal effect (below 1.5 pp) is outside what any tested threshold can see. The files do not give a business reason for 2 pp. I could not check whether `02` or `04` justify it, because I did not read them.
- A trend plus seasonality can break strict alternation in one transition and still be a seasonal pattern on average. The rule uses the smallest of six aligned shifts (the margin), so one off transition fails the whole genre. Sci-Fi & Fantasy's mean aligned shift in check 1 is 1.85 pp with bootstrap CI [0.33, 3.46] (`05_analysis.md`, table). That interval excludes zero. On an average-based measure this is the one genre with some evidence of alternation. The insight reports only the margin (0.49 pp) and not this.

### 2. Confounders, selection and measurement
- The genre groups may hide genre-level seasonality. 57.0% of labelled hours (54.3% of keys) get a group different from the first-listed IMDb genre (`05_analysis.md`, "Group coarseness"). Mean shares are Crime & Thriller 30.94% and Drama 4.88% (`05_analysis.md`, `06_validation.md` N2). My inference: Drama is normally a very common IMDb genre, so a 4.88% share suggests the priority table moves most of it into other groups, mainly the 30.94% Crime & Thriller bucket. A large catch-all group can average away opposite seasonal movements inside it. The analyst calls label sensitivity "the largest uncontrolled choice" (`05_analysis.md`, suggestions), and no alternative mapping was run.
- The scope is a fixed union of 4,398 keys chosen by the top 80% of hours in any half. The per-half scope was not run (`05_analysis.md`, "Scope and labelling"). Titles are selected on viewing hours, so the sample is built from the same outcome the shares measure.
- The shares are shares of hours, so a single huge title in any half pushes every other genre's share down. This adds noise to the shifts independently of seasonality (my inference, consistent with I2).
- Matching errors may be non-random. 725 keys were ambiguous, and 668 of them were resolved by "most votes" (`05_analysis.md`). A rule that favours popular works can systematically pick older or better-known works with a different genre. The validator's 98.0% agreement (351 of 358) comes from a simpler route that shares the same "most votes" logic, so it is not a strong test. Seven keys differed (`06_validation.md` N1).
- Unlabelled hours grow from 3.08% to 4.49% of in-scope hours over the period (`05_analysis.md`). Tagged titles are less often matched, especially early: -4.1 pp in H1 2023 against -0.9 pp in H1 2026. If coverage changes with time, it can add a drift that looks like a shift. Post-stratification changes margins by "at most a few tenths of a pp", so this is probably minor. It only handles the language tag, not other reasons for non-matching.

### 3. Data limits
- Seven half-years give six transitions and only three H1-to-H2 pairs. Any estimate of a yearly cycle rests on three full cycles. The permutation null assumes exchangeable positions, and the analyst flags this as imperfect when trends exist (L3).
- The "new" stratum is small (1.6e10 to 2.0e10 hours against 5.9e10 to 6.4e10 carried, `variant_hours.csv` via `05_analysis.md`) and its margin CIs are very wide, for example Crime & Thriller [-17.47, 3.11]. Check 3 new therefore cannot confirm or refute anything. Yet a pass requires all four checks, so noise in that stratum alone can block a pass.
- The data come from Netflix half-year reports with a listing threshold. Titles below it are missing. Hours of a title that straddles two halves are split by the report, not by release season. Hours measure what Netflix released and licensed (as I1 notes), so "seasonal viewer demand" is not what the data can measure.
- Cleaning merges different works with the same title into one key (Monster, Maria, War Machine, `06_validation.md` N3). The hours are small but the effect on labels is unknown.

### 4. What would overturn the conclusion, and how to check
- Show that the rule detects a planted seasonal pattern. For example, add a known alternation of 2 pp to synthetic or permuted shares and check that the pipeline passes it. If it fails, the null is not informative. This would need new code and is not in the files.
- Re-run with a different mapping, such as the first-listed IMDb genre, or with Drama treated as its own eligible group, and see whether any margin passes. The 57.0% relabel rate means this is the likeliest change that could alter the result.
- Use a per-half scope instead of the union scope.
- Test a looser, average-based statistic (for example the mean aligned shift with its bootstrap CI) alongside the min-based margin. Sci-Fi & Fantasy at 1.85 pp [0.33, 3.46] is where this would matter.
- Hand-verify the 725 ambiguous keys, prioritising the high-hour ones. A sizeable error rate there would change the interpretation.

### 5. Claims beyond the analysis
- "Recomputed independently" (Evidence line 1): `06_validation.md` "Limits of independence" says cleaning, key building and IMDb matching were reused from the analyst. A bug there is caught only by the 98.0% spot check. The insights' verification note does mention this, but the evidence lines say "independently".
- The interpretation says "this data does not support planning the H2 genre mix from last year's H1-to-H2 shifts". The data show that a very strict rule failed. They do not show that last year's shift has no predictive value, and no prediction test was run (`05_analysis.md` L7: chart 6 not produced).
- The instruction to use "the latest half-year mix as the baseline" is not tested here. The latest half has the highest unlabelled share, 4.49% in H1 2026 (`05_analysis.md`). If I2 is right that a few titles drive shares, the latest half is the most exposed to its own blockbusters. I1 and I2 pull against each other on this.
- Dismissing the all-checks p = 0.039 while citing the check-1 p = 0.138 is explained in the text, but the two permutation setups differ (5,040 orderings against 720 with H1 2023 fixed). A reader may see this as picking the p-value that fits. The explanation, a negative observed margin, is sound and matches `05_analysis.md`.

## I2: "Large single-genre shifts are mostly driven by a few big titles"

### 1. Alternative explanations
- Big-title timing may itself be the seasonal pattern. If large releases tend to land in the same half each year, removing the top 10 per half (check 2) removes the seasonal signal by construction. Check 2 cannot separate "no seasonality" from "seasonality carried by tentpole titles". The files do not say whether Stranger Things and Wednesday recur in a predictable half. (My inference.)
- A title can get big because of the genre or franchise effect (the sequels, season launches). Then "driven by titles" and "driven by genre" are not exclusive.
- The Sci-Fi & Fantasy rise (+4.86 pp) and fall (-3.60 pp) can both be a normal release-cycle effect: a season is released, it peaks and its hours then fall away in the next half. This is a title life cycle, not a genre pattern, but it is also not random.

### 2. Confounders and measurement
- The claim covers all genres ("large single-genre shifts in this data") but the evidence is one genre in one transition. Other large shifts named in `05_analysis.md`, Crime & Thriller -2.79 pp (H1 2023 to H2 2023) and +2.69 pp, are not attributed to any titles.
- The shares are of in-scope hours, so a big title in one genre lowers every other genre's share. Part of any large shift in other genres is mechanical.
- Genre assignment of the two titles depends on the priority table (57.0% of labelled hours differ from the first IMDb genre). Whether these titles are Sci-Fi & Fantasy under another mapping is not shown.

### 3. Data limits
- Only the two titles' raw hours are given: Stranger Things 0.40e9 to 2.49e9 and Wednesday 0.09e9 to 1.28e9 (`06_validation.md` section 4). No file gives their share of the +4.86 pp move, so "mostly" has no number behind it. The author admits this ("I did not test it separately").
- The top-25 test is the validator's own extra check (`06_validation.md` N4: "not part of the verdict"), and it is reported only for check 1 margins ("all below 0.21 pp"). It shows that margins stay small after removing titles. It does not show that the removed titles caused the original shifts.

### 4. What would overturn it, and how to check
- Compute, for each large shift (the four named in `05_analysis.md`), the change in the genre share with and without the leading titles. If the shift survives after removing the top 10 or top 25 titles, the claim fails for that shift.
- Check whether the removed titles are concentrated in the same half across years. If so, the big-title explanation is a seasonal explanation.
- Check the claim for a genre other than Sci-Fi & Fantasy, such as Crime & Thriller.

### 5. Claims beyond the analysis
- The insight has a PASS label on the numbers only. The causal claim ("driven by") rests on one example and an untested hypothesis, which the interpretation partly admits.
- "Planning around specific big releases matters more than planning around genre" is a business conclusion. Nothing in `05` or `06` compares the two, and the 02 decision rule is not tested against any alternative. This goes beyond the evidence.
- The pass of check 2 "removes it" shows only that the rule's margin falls from +0.49 (check 1) to -0.54 (check 2) for Sci-Fi & Fantasy, with CIs [-2.04, 1.12] and [-2.80, 0.22]. Both intervals include zero, so the difference between the two margins is well within the noise.

## Cross-cutting
- The human did not reproduce the key numbers (07 verification note). The pilot match check was AI-only (L1). The validator reused the analyst's matching code. So the chain from raw titles to labels has no fully independent human check.
- I could not see `02`, `04` or `01`. If they justify the 2 pp threshold or the priority table, some objections above weaken. I did not look.

## Ranked strongest objections
1. The rule has almost no power: 0 of 5,040 random orderings pass at 2 pp and only 24 at 1.5 pp (`05_analysis.md`, `06_validation.md`). The null in I1 is therefore weak evidence, and the insight does not say so.
2. Genre groups come from a priority table that changes the group for 57.0% of labelled hours (`05_analysis.md`). Drama is only 4.88% while Crime & Thriller is 30.94%. Seasonality inside a coarse catch-all group can be hidden, and no alternative mapping was run.
3. I2 asserts a cause ("driven by a few big titles") from one genre and one transition, with no decomposition. Check 2 also cannot tell apart big titles from seasonally scheduled big titles.
4. The checks block a pass with noise: the "new" stratum is small and its margin CIs are 10 to 20 pp wide (`06_validation.md` section 4). A single all-or-nothing rule across four checks lets the noisiest check decide.
5. Sci-Fi & Fantasy's mean aligned shift of 1.85 pp [0.33, 3.46] (`05_analysis.md`) points the other way on an average-based view, and I1 leaves it out.
6. The label chain is not independently verified: AI-only pilot, 725 ambiguous keys unchecked by hand, validator reuses the matching code, and "most votes" tie-breaks favour popular works (`05_analysis.md`, `06_validation.md`).
7. The planning advice reaches beyond the data: no prediction test was run, and the "latest half as baseline" choice is exposed to the same big-title swings that I2 describes, in the half with the highest unlabelled share (4.49%).
8. Scope and coverage choices (union scope, unlabelled hours rising from 3.08% to 4.49%, tagged titles matched less often) were checked only on the language tag.
