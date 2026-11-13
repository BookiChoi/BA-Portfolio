Author: ai/analyst

# 04 Analysis plan: Netflix engagement (as-of 2026-11-12)

Status: DRAFT, awaiting human review. No code has been written and no analysis has been run. Nothing below contains a result. All "to confirm" items are facts I could not check without opening the files, which Phase A does not allow.

Scope: only Q1 exists in `02_questions.md`. Inputs: `02_questions.md`, `03_data_plan.md` (including the Gate 1 decisions) and `data_manifest.json` (seven xlsx files, stored outside the repo in `~/Downloads/netflix-reports/`, read-only).

## Global settings (apply to Q1)

| Item | Setting | Why |
|---|---|---|
| Alpha | 0.05, family-wise | One decision per genre tested, several genres, so the error rate is controlled across the family, not per genre. |
| Multiple-comparison correction | Primary: permutation-based family-wise error (max-type, over all tested genres). Reference only: Bonferroni, alpha / G (G = number of genres tested). | Gate 1 asks for the chance of a spurious pass across all genres. A permutation keeps the "shares sum to 100%" dependence between genres, which Bonferroni ignores. Exact enumeration is feasible (see Q1 step 7). |
| Random seed | 20261112 for every stochastic step (bootstrap, pilot sampling, tie-breaks) | Reproducibility. The permutation test is exact, so it needs no seed. |
| Libraries | pandas, numpy, scipy, matplotlib, openpyxl, requests; versions recorded in `05_analysis.md` | Required by the pipeline rules. |
| Code layout | `pipeline/load.py`, `clean.py`, `genre.py` (TMDB lookup), `analyze.py`, `visualize.py`; `main.py` runs end to end; tests in `tests/` | Repo CLAUDE.md. Plot functions return a Figure and never call `plt.show()`. |
| Outputs | Each PNG has a CSV/JSON of its aggregated data beside it, under `outputs/` | Web presentation needs aggregates only. Raw data and TMDB responses stay out of git. |
| Secrets | TMDB key is read from an environment variable set outside the repo. It is never printed, logged or written to a file. | Gate 1. |

## Q1: Does any genre alternate by half-year (H1 to H2 up, H2 to H1 down, or the reverse) by at least 2 pp every time?

### 1. Metric definitions (all follow `02_questions.md`)
- Unit: one genre group in one half-year, seven half-years (H1 2023 to H1 2026).
- Title key: a cleaned title with season, language and year tags removed. Hours of all rows with the same key within a half-year are summed, so a series counts once.
- Genre share(g, t) = hours of labelled titles in group g in half-year t / hours of all labelled titles in t.
- Labelling coverage(t) = labelled hours / all hours in file t. Unknown hours are reported per half-year and excluded from the denominator.
- Shift d_k = share(t+1) - share(t) in pp, six consecutive pairs. Odd k = H1 to H2, even k = H2 to H1.
- Alternation sign s_k = +1 for H1 to H2 and -1 for H2 to H1. A genre has phase +1 if s_k * d_k >= 2 pp for all six k (rises in H2, falls in H1), and phase -1 if s_k * d_k <= -2 pp for all six (the reverse). Pass of one check = phase +1 or -1 with every |d_k| >= 2 pp.
- Genres tested: those whose mean share over the seven half-years is at least 5%, after mapping to 6 to 8 groups.
- Check 1: all labelled titles.
- Check 2: remove the 10 title keys with the most hours in each half-year (chosen per half-year; recompute the denominator after removal).
- Check 3: split labelled titles into New (key absent from the previous half-year's file) and Carried over (key present). Compute shares within each stratum (genre hours in the stratum / labelled hours in the stratum). Five transitions, H2 2023 to H1 2026. Pass = the pattern with every |d_k| >= 2 pp in both strata. The phase of the two strata and of check 1 must be the same, otherwise the genre does not pass (my reading; see "Points for the human to confirm").
- Overall pass = pass in checks 1, 2 and 3 in the same phase.
- Sensitivity only (not the decision): the same logic at 1.5 pp and 3 pp.

### 2. Data fields used
From each Netflix xlsx: title, hours viewed, the sheet or column that separates movies from shows, and premiere date if present (only for the pilot's match check). Column names are not yet confirmed (03 lists them as "to confirm"). The first Phase B step profiles all seven files and writes the actual names, sheets and layout differences to `05_analysis.md`. If the layout differs between halves, I map it to a common schema in `clean.py` with a comment for each decision.
From TMDB (genre only): title, original title, original language, first air or release date, genre ids.

### 3. Cleaning policy (missing values, outliers, duplicates)
- Rows labelled "Other Movies" or "Other Shows" (aggregate rows with no title, per the manifest notes): excluded from all share calculations, counted as unlabelled hours in the coverage figure. To confirm at profiling that they carry hours.
- Missing or non-numeric hours: row dropped, count and hours reported per file. Missing title: row dropped and counted. No imputation, because imputing viewing hours would create hours that Netflix did not report.
- Hours of zero or negative: flagged, reported, dropped.
- Titles below Netflix's reporting threshold are not in the files, so shares are among listed titles only (limitation, stated in the output).
- Duplicates: same key within a file is summed (series seasons). Keys that collide across different titles (for example a remake with the same name) are listed and checked by hand when they are in the labelled scope.
- Outliers: no trimming or winsorising in the primary analysis. A few very large titles are real viewing and are the main reason a genre moves. Check 2 is the planned robustness test for them. Any change to this needs a human decision.
- Title-key quality: print the 50 largest-hour keys per half-year and 50 random ones for visual check. Report the cross-half match rate (share of keys and of hours in a half-year that appear in the previous one) and compare English and non-English titles.

### 4. Labelling scope (rule fixed here, N computed in Phase B before any lookup)
- For each half-year, rank keys by hours and compute the cumulative share of all hours (including unlabelled). Save this curve as a chart and CSV.
- Scope N = the smallest per-half-year top-N such that the union of those lists covers at least 80% of total hours in every half-year. The union is labelled, so a title that is large in only one half is still labelled. The 80% target is my proposal; the human can change it before approval. I will not tune it after seeing genre shares.
- Report N, the number of unique keys to look up (the API cost) and the hours coverage. If the key count is unreasonable for the TMDB limits, stop and ask rather than lowering the target.
- Top-10 removal in check 2 uses only titles inside the scope (by construction they are).

### 5. Genre labelling (TMDB, non-commercial, attribution shown in README/About)
- Approved endpoints (base `https://api.themoviedb.org/3`): `/search/movie`, `/search/tv`, `/movie/{movie_id}`, `/tv/{series_id}`, `/genre/movie/list`, `/genre/tv/list`. No other endpoint is used. Exact parameters and rate limits to be checked against the TMDB API docs before the first call.
- Matching rule (written before the pilot): use the movie or show type from the report; search the cleaned title; for titles with two language parts, try each part; accept a result when the normalised title equals the title or original title and, where the report gives a premiere date, the release year is within 1 year; otherwise take no match. No fuzzy match below that rule. Unmatched titles stay unlabelled.
- Primary genre = the group with the highest priority among the title's TMDB genres, using a priority-ordered mapping table `config/genre_mapping.csv` written and committed by the human before any share is computed. I will not write or edit it. The mapping must cover every id in the movie and TV genre lists, so an unmapped id stops the run. I record the file's sha256 and git commit, and check that the commit is earlier than the first share computation.
- Pilot: 30 titles, 15 English and 15 non-English, random from the scope (seed fixed), reported with the match rate and Wilson 95% CI (n = 30 gives a wide interval; I say so). Correct match = rule above satisfied and the 30 matches printed for a human spot check. If the match rate is below 85%, stop and revise the matching method before the full run.
- Full run: all keys in scope, responses cached outside the repo.
- Coverage rule (Gate 1): if the unlabelled hours exceed 10% of a half-year's hours within the scope, in any half-year, Q1 is reported as inconclusive. I still produce the numbers but label them as inconclusive.
- Language bias: match rate by language group (TMDB original language for matched titles; for unmatched titles, a rule based on the "//" tag and script, to confirm at profiling), as a risk difference with a 95% Wilson CI per group and a chi-square or Fisher exact test (alpha 0.05, reported as a descriptive check, not corrected). Also report the hours-weighted match rate.

### 6. Method, why, assumptions
- Method: compute shares for the three check versions, compute shifts, evaluate the pass rule, and compare with a permutation null. Descriptive and rule-based, because the question is a deterministic pattern with seven points per genre, too few for a time-series model. A seasonal model (for example seasonal decomposition, ARIMA) would need many more periods than 7.
- Assumptions: (a) the genre mapping and primary-genre rule are fixed before computing, (b) report files are comparable across halves (same threshold and definition), unverified, (c) title keys identify the same show across halves, (d) unlabelled hours are not biased in a way that creates the alternating pattern; I report coverage per half-year so the human can judge, (e) hours are the whole set of listed titles, not a sample, so confidence intervals describe sensitivity to title-level composition, not sampling from a larger population.

### 7. Statistical tests, effect size and confidence intervals
1. Pass/fail table for every genre, check and phase, with all six (or five) shifts in pp.
2. Effect size per genre and check: (a) mean alternating amplitude A = mean(s_k * d_k) in pp, with its sign giving the phase; (b) smallest |d_k|. The planning figure in the decision rule ("average observed shift") is mean |d_k|, reported as the same number with its interval.
3. Confidence intervals: 95% percentile bootstrap, 2000 resamples. Resample title keys with replacement within each half-year (same seed), recompute shares, shifts, A and the pass indicator. Report CI for each shift, for A, and the share of resamples in which the genre still passes (stability). Because shares are population values for listed titles, this CI shows how dependent the result is on a few titles. It is not a population inference. As a secondary figure, a t-interval on the six s_k * d_k values (df = 5) is shown; it is weak and is labelled as such.
4. Spurious-pass probability (Gate 1 requirement): for the observed set of seven genre-share vectors (all genres, summing to 100% in each half-year), enumerate all 7! = 5040 orderings of the half-years, keeping each half-year's whole composition together (this keeps the dependence between genres). For each ordering apply the same pass rule at the same threshold. Report (a) the probability that at least one tested genre passes check 1, which is the family-wise false-pass rate under "no time structure"; (b) the same for checks 1 and 2 jointly (the same ordering applied to both composition tables); (c) the null distribution of the number of passing genres, and the observed count's position in it (exact p = share of orderings with at least as many passing genres). For all three checks jointly, check 3 has only five transitions with H1 2023 missing, so I report (c) separately by enumerating the 6! = 720 orderings of H2 2023 to H1 2026 and applying all three checks on the five transitions; the three-check probability is also bounded above by (b). The genre set tested in the null is the set fixed from the observed data (mean share >= 5%), which I note as an approximation.
   Observed orderings are one of the 5040, so the observed pass is not "significant" at alpha 0.05 unless its exact family-wise p is below 0.05. I report both the rule-based pass (what the decision rule uses) and this p. A pass with p >= 0.05 is reported as a weak lead.
5. Bonferroni reference: 0.05 / G, shown next to the permutation p for context only.
6. Pairs: passing genres whose shift series have Pearson r <= -0.9 over the six shifts (mirror movement, mostly a consequence of the sum-to-100% constraint) count as one finding. The -0.9 cut-off is my proposal; the human may change it.
7. Sensitivity (not decision): repeat the pass table at 1.5 pp and 3 pp. Also repeat check 1 with scope target at 70% and 90% only if the human approves; I will not add this on my own.
8. Any pass is reported as a lead to re-check, as Gate 1 requires, not as a confirmed seasonal law. The result is reported even when there is no pass.

### 8. Expected charts (PNG + CSV/JSON in `outputs/q1/`)
1. Cumulative hours share by rank, per half-year, with the chosen N marked (supports scope).
2. Coverage chart: labelled, unlabelled and out-of-scope hours per half-year (stacked bar), plus match-rate-by-language chart.
3. Genre share lines over seven half-years, one small panel per tested genre, H1 to H2 segments shaded alternately, 2 pp threshold shown as a band around the previous point.
4. Heatmap of shifts d_k (genre x transition), one panel per check (all, excluding top 10, new, carried over), cells below 2 pp in absolute value or with the wrong sign greyed out.
5. Permutation null: histogram of the number of passing genres, observed value marked.
6. Bootstrap interval plot of A per genre per check.
Each chart gets one takeaway line, limitation line, and the aggregated data path in `05_analysis.md`.

### 9. Deliverables in Phase B (`05_analysis.md`)
Question, method, chart path, aggregated data path, one-line takeaway, limitations and the evidence (script path plus log or output) for every number. No insight or recommendation text; those belong to the human. A dated H2 2026 prediction is the human's to write; if there is a pass, I only supply the mean |shift| and its interval.

## Points for the human to confirm before approval
1. Check 3 reading: shares within each stratum (New, Carried over), and the pass must be in the same phase as check 1. The alternative is each stratum's contribution to the total share, which is a stricter test and would give smaller shifts.
2. Scope target: 80% of hours in every half-year via the union of top-N lists.
3. Pair rule: r <= -0.9 counts as one finding.
4. Language group for unmatched titles: how to decide it is not defined in the files; I will propose a rule at profiling.
5. The path `config/genre_mapping.csv` for the mapping table; it must exist and be committed before Phase B reaches the share step. If it is missing, I stop.
6. The null set: the permutation uses the genre set selected from the observed data, so it slightly understates the selection effect.

## Known limitations to carry into the results
- Seven half-years is a small sample; the alternating pattern has a non-trivial false-pass chance even at 2 pp, which is why the permutation estimate is required.
- Shares reflect Netflix's release and licensing slate, not viewer demand.
- Labelling covers the scope only and may be biased against non-English and licensed titles.
- New/carried over is presence in the previous file, not release date. Renamed titles can be misclassified as new.
- The yearly report format from 2027 may make a dated H2 2026 prediction impossible to score.

<!-- Approval line intentionally absent: only the human may add it. -->
