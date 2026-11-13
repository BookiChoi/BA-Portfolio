Author: ai/analyst

# 04 Analysis plan: Netflix engagement (as-of 2026-11-12)

Status: draft, awaiting human review. No code has been written and no analysis has been run. Every number in 05_analysis.md will come from executed scripts with the log path recorded. Nothing below is a result.

Inputs read: workflow/02_questions.md, workflow/03_data_plan.md (including the Gate 1 decisions and the IMDb amendment), data_manifest.json. I did not open the data files, so all column names are "to confirm at profiling".

## Scope
Only Q1 exists. The plan has a data-preparation section (P1 to P5, fixed before any share is computed) and then the Q1 analysis.

## Global settings (apply to everything)
| Item | Setting | Why |
|---|---|---|
| Random seed | 42 for bootstrap and pilot sampling. Permutation tests use exact enumeration, so they need no seed | Reproducibility |
| Alpha | 0.05, one family-wise level for the permutation test (see Q1 section) | One decision, one error budget |
| Multiple comparisons | The permutation statistic is a maximum over all eligible genres and both directions (max-statistic method). It controls the family-wise error rate across genres without Bonferroni | Genres are not independent (shares sum to 100%), so Bonferroni would be wrong in both directions |
| Effect size | Mean aligned shift in pp (defined below), with its 95% CI, plus the pass margin in pp | Never report p-values alone |
| CI method | Cluster bootstrap over title keys, 2,000 replicates, percentile 95% interval | A title keeps its hours across halves, so keys must be resampled jointly |
| Libraries | pandas, numpy, openpyxl, matplotlib, scipy. Versions recorded in 05_analysis.md | Required by the pipeline rules |
| Data location | Raw xlsx and IMDb files stay outside the repo (paths in data_manifest.json). The IMDb files get manifest entries (URL, download date, rows, sha256) before use | Data rules |
| Outputs | Each PNG has a CSV/JSON of its aggregated data next to it, in `outputs/q1/` | Web rendering; no raw data exported |
| Code layout | `pipeline/load.py`, `clean.py`, `label.py` (IMDb matching), `analyze.py`, `visualize.py` (Figure-returning, no `plt.show()`), `main.py`, tests on synthetic data | Repo CLAUDE.md |

## Data preparation (fixed before any genre share is computed)

### P1. Load and profile
- Read all sheets of the seven xlsx files. Confirm per file: sheet names, column names, row counts against data_manifest.json, and layout differences.
- Fields used: title and hours viewed. Release date is read only if present, for matching (P3).
- "Other Movies / Other Shows" rows are aggregates, not titles. They are excluded from the genre share and counted in "all hours" for labelling coverage.
- H1 2023 has no movie/show split. Rows are read from its single list. A row's type is inferred in P3.

### P2. Clean and title key
- Key = lowercased title with season, part, chapter and "limited series" tags, trailing year tags and the language tag removed. The exact regex list is written and unit-tested before the pilot.
- Language rule: Netflix lists non-English titles as "Original // Translated" (to confirm at profiling). A row is "tagged" if the raw title contains " // ", otherwise "untagged". The key is built from the first segment. The other segments are kept as alternate match candidates (P3). This tag is the only language proxy. No title is assigned a genre by language.
- Rows with the same key in one half-year are summed (seasons become one series; this also gives the "one title" rule for check 2). Count of merged rows and of movie/series key collisions is reported.
- Missing or non-numeric hours: row dropped and counted. Zero or negative hours: stop and report. Duplicated full rows: reported, then merged by sum only if the profile shows they are distinct seasons; otherwise stop and ask.
- Outliers: no winsorising and no deletion. Very large titles are real viewing and are handled only by the planned check 2.

### P3. IMDb matching (written down and frozen before the pilot)
Files: title.basics.tsv.gz, title.ratings.tsv.gz, and title.akas.tsv.gz as a second-stage fallback only. Reason for akas: Netflix often uses the English or regional title for non-English content, which can differ from IMDb primaryTitle and originalTitle. This stage is fixed up front for every title, not added after seeing the pilot.
Rules, in order:
1. Normalise both sides the same way (lowercase, strip punctuation and accents, collapse spaces).
2. Stage 1: candidates whose normalised primaryTitle or originalTitle equals the key. Stage 2 (only for keys with no stage 1 candidate): candidates whose akas title equals the key. For tagged rows, try segment 1, then the remaining segments, with the same two stages.
3. Type filter. Where the file gives a movie/show split: movie rows use movie, tvMovie, tvSpecial; show rows use tvSeries, tvMiniSeries. H1 2023 rows without a split use "series" if a season tag was stripped, otherwise all of those types.
4. Year filter when the release date exists (earliest listed date for the key): movies need |startYear - release year| <= 1; series need startYear <= release year + 1 (a later season premiere is after the series start). No year filter when there is no date.
5. Tie-break: highest numVotes (ratings file), then lowest tconst, so the result is deterministic.
6. Genre: IMDb genres (up to three) go through the human's priority-ordered mapping table to one group. A title with no mappable genre, or with no match, is "unlabelled".
Each key records: matched tconst, stage, candidate count, tie-break used, group. Candidate count > 1 is reported as ambiguity.

### P4. Labelling scope (set from hours only, before any labelling)
- For each half-year, sort keys by hours and compute the cumulative share of listed-title hours.
- Try cumulative targets 90%, 85%, 80% in that order. Use the first target for which the union of keys across the seven halves has at most 3,000 unique keys. If even 80% exceeds 3,000, stop and ask (Gate rule).
- The chosen target and key counts are written to the log before labelling starts. All three checks use this same scope. Keys outside the scope are not labelled and sit outside the share denominators (reported as hours not in scope).
- The top-10 titles per half-year are always inside the scope.

### P5. Pilot, coverage and bias report
- Pilot: 30 keys drawn at random (seed 42) from the scope, 15 tagged and 15 untagged. Report the unweighted match rate and a table of the 30 (key, matched title, year, type, genres, group) for the human to hand check. I will mark my own agree/disagree per row, but the human check is the authority.
- If the pilot match rate is below 85%, stop. Do not label the full scope. Report to the human, who decides on a change to matching (the stages above are the only pre-agreed ones).
- Full labelling: report match rate and labelled-hours coverage per half-year (labelled hours / all listed hours, and labelled hours / in-scope hours), overall and by tagged vs untagged, as proportion differences with 95% Newcombe CIs.
- Coverage rule: if unlabelled hours exceed 10% of in-scope hours in any half-year, Q1 is reported as inconclusive. The computed shares are still shown, marked inconclusive.

## Q1: Does any genre alternate by half-year?

### Metric definitions
- Genre share s(g,t) = hours of labelled titles in group g in half-year t / hours of all labelled titles in t, in percent. t = 1..7 for H1 2023 ... H1 2026. Unlabelled hours are excluded from the denominator and reported separately.
- Shift d_i = s(t+1) - s(t) in pp, i = 1..6. Odd i are H1 to H2 transitions; even i are H2 to H1 transitions.
- Eligible genres: average of the seven shares >= 5% under check 1. This set is then fixed for checks 2 and 3 and all sensitivities.
- Directional margin for a variant c and direction "up" (peaks in H2): min(d1, d3, d5, -d2, -d4, -d6). For direction "down" the signs flip. Pass at threshold theta (2 pp) means margin >= theta in the same direction. A tolerance of 1e-9 is used and near misses within 0.05 pp are listed.
- Check 1: all labelled titles, six transitions.
- Check 2: per half-year, drop the 10 keys with most hours (all listed keys, labelled or not; series already merged by P2), then recompute shares. The numerator and denominator both lose them.
- Check 3: split labelled titles in each half-year from H2 2023 on into "new" (key absent from the previous half-year's cleaned file) and "carried over" (present). Shares are within each stratum. Five transitions (d2..d6). Both strata must pass, in the same direction as in checks 1 and 2.
- Genre pass = a single direction whose margin is >= theta in check 1, check 2, check 3 new and check 3 carried. Genre margin = max over direction of min over those four margins.
- Effect size: mean aligned shift = mean of the six aligned shifts (d1, d3, d5, -d2, -d4, -d6 for up), in pp, check 1 only, with the bootstrap CI. This matches the decision rule's "average observed shift". For check 3 the five-transition mean is reported per stratum.

### Method and why
Direct computation of the pre-registered pattern, because Q1 is a deterministic rule on seven points, not an estimate from a sample. Inference is added in two ways:
1. Cluster bootstrap CI (title keys resampled with replacement, jointly across halves; top-10 sets and new/carried membership held fixed at their observed values) for each shift, the mean aligned shift, and the margin. Also the bootstrap fraction of replicates in which the genre passes. This shows how dependent the result is on a few titles. It does not describe viewer sampling, since the reports are near-complete counts.
2. Family-wise permutation test for the "spurious pass among all tested genres" question the human asked for. Null: the order of the half-years carries no calendar signal. Under the null, the seven half-year share vectors (all genres together, so cross-genre dependence and the 100% constraint are kept) are exchanged among positions. Statistic: M = max over eligible genres of the genre margin. p = share of orderings with M >= observed M. Alpha 0.05.
 - Check 1 only: all 7! = 5,040 orderings.
 - All checks together: H1 2023 has no strata, so only orderings that keep H1 2023 in position 1 (6! = 720) are used, with checks 1 and 2 on all seven positions and check 3 on positions 2 to 7. The permuted vectors are the precomputed variant shares, so check 3 strata keep their real new/carried definitions. This is stated as a limitation: the strata depend on file order.
 - Also reported: the number of orderings with any pass at theta (the family-wise spurious pass probability), and the single-genre reference 2 x (1/2)^6 = 3.1% from the question.
 - The permutation test is supplementary. The decision rule stays as written in 02_questions.md: a pass on all three checks. The human decides how to weigh a pass with p >= 0.05. Per Gate 1, any pass is reported as a lead to re-check.
- Pair rule: among passing genres, compute Pearson r between their six shifts (check 1). Pairs with r <= -0.9 count as one finding (connected groups). Report the number of passing genres before the rule and the number of findings after it. With only six shifts, r is itself noisy; stated as a limitation.
- Sensitivity only (not the decision): theta = 1.5 and 3 pp for all of the above; (b) post-stratification of check 1 by tagged/untagged coverage (reweight so each language group's labelled hours match its in-scope hours), to see whether unequal match rates by language change a pass. Nothing else is varied.

### Assumptions
- A report's hours are comparable across halves (same definition and listing threshold; the 50,000-hour threshold and its consistency are unverified until profiling).
- One primary genre per title, fixed across halves, from IMDb genres through the frozen priority table. Genre mislabelling is not random, which the pilot hand check only partly shows.
- Key matching across halves is reliable. A new season of a carried-over series counts as "carried over" because the season tag is stripped; this follows Q1's wording but means "new" is mostly new series and licensed additions.
- Mean share equal weighting across halves defines eligibility.
- Positions are exchangeable under the permutation null. Real trends and autocorrelation violate this somewhat (a trend works against alternation, so the test is not expected to be too liberal for this pattern, but it is not proven).

### Statistical tests and reporting
- Required: cluster bootstrap CI (shifts, mean aligned shift, margins, pass frequency); permutation max-statistic test at alpha 0.05; Newcombe CI for match rate differences.
- Effect size and CI reported for every genre: the six shifts, margin per check, mean aligned shift and its 95% CI. No p-value appears without them.
- Missing values and outliers: as in P2 and P5. Unlabelled and out-of-scope hours are reported, never imputed. No outlier removal except the planned top-10 exclusion.

### Data fields used
Netflix: title, hours viewed, (release date, movie/show sheet if present). IMDb: tconst, titleType, primaryTitle, originalTitle, startYear, genres, numVotes; akas: titleId, title. External: the human's frozen genre mapping table (I will check with git history that it was committed before any share computation; I have not read it for this plan).

### Expected charts (PNG + CSV/JSON in outputs/q1/)
1. Line chart: share by half-year for each eligible genre, H1/H2 shading, check 1 (all titles).
2. Shift bars: six shifts per eligible genre with the +/-theta band marked, one panel per genre.
3. Check matrix: genre x (check 1, check 2, check 3 new, check 3 carried) showing margin in pp and pass/fail, with the bootstrap CI of the margin.
4. Permutation null: histogram of M with the observed M and alpha line.
5. Coverage and matching: labelled-hours coverage per half-year, and match rate tagged vs untagged with CI.
6. If a genre passes: a dated H2 2026 prediction table (expected shift = mean aligned shift, CI, date written). Scoring is outside this project run. Not produced if nothing passes.

### Limitations to carry into 05_analysis.md
Shares reflect Netflix's own slate, not viewer demand. Only seven half-years. IMDb primary genre by priority table is a coarse label. Right-censoring: the H2 2026 prediction may not be scorable if Netflix's yearly snapshot does not allow derivation.

## Open points for the human (answers change the plan; none blocks approval)
1. Check 3 reading: I require both strata to pass, in the same direction as the other checks. If you meant either stratum, say so.
2. Scope target: 90/85/80% fallback list is my choice; you may prefer a fixed value.
3. The akas second stage is an addition I am proposing under your amendment; remove it if not wanted.
4. Permutation null (exchange of half-year order) is my choice of "chance of a spurious pass"; alternatives such as label shuffling across titles are possible.
5. The git status shows a modified file under workflow/archive/run1/; I did not touch it.

## Human decisions at Gate 2 (2026-11-12, revised plan)
- Check 3: both strata must pass, in the same direction as checks 1 and 2, as planned.
- Labelling scope: cumulative targets 90%, 85%, 80% in that order, at most 3,000 unique keys; if even 80% exceeds 3,000, stop and ask.
- The title.akas second stage is approved. IMDb files are in ~/Downloads/imdb-datasets/ (outside the repo). Record URL, download date, rows and sha256 for each in data_manifest.json before use.
- Permutation null: exchange of half-year order, as planned, reported as supplementary. A pass with p < 0.05 is a stronger lead; a pass with p >= 0.05 is a weak lead. Neither is a confirmed seasonal law.
- Mapping table: Projects/netflix-engagement/config/genre_mapping.csv with columns imdb_genre, group, group_priority, committed by me before the pilot. The analyst does not edit it. Before matching, list all distinct genre values in title.basics.tsv.gz and stop if any is not in the mapping. An empty group means "not mappable" (a title with only such genres is unlabelled).
- Year hint: when a title carries a year tag, for example "Suits (2011)", use it as the release-year hint. Movies need |startYear - tag year| <= 1; series need |startYear - tag year| <= 1. If a release date exists, the date rule in P3 applies instead. This rule is fixed before the pilot.
- Pilot stop: write the 30-row pilot table to outputs/q1/pilot_table.csv, add a short status note to 05_analysis.md, and stop before labelling the full scope. I will hand check the 30 rows and record my result in workflow/05_pilot_check.md. Continue only after that file exists.
- Add to the limitations: the "new" stratum includes titles that first crossed the report's listing threshold, not only newly released ones; the hours are reported at coarse resolution with many ties.
- The superseded plan under workflow/archive/run1/ is not used.
- Everything else in this plan is approved as written.

## Human decisions at Gate 2, amendment 1 (2026-11-12)
- Scope cap: raised from 3,000 to 4,500 unique keys. The 3,000 cap was set when genre labels were to come from an API with call costs; with local IMDb files the cost is compute only. This is decided after seeing the scope sizes (7,342 / 5,548 / 4,287) but before any pilot, label or genre share exists. The 80% target is used. If the union exceeds 4,500 after any key-rule change, stop and ask.
- Tagged titles (" // "): as implemented. For all segments, stage 1 (title.basics) is tried first; only keys with no stage 1 candidate from any segment go to stage 2 (title.akas). If segments give different stage 1 candidates, prefer a candidate that matches more than one segment, then apply the vote tie-break, and record it as an ambiguity.
- Key: the key includes the media type (movie or show) wherever the file gives it. H1 2023 has no type: its type is taken from the H2 2023 file when the cleaned title appears there with exactly one type, otherwise "unknown" and matched as in P3. For the new / carried-over split in H2 2023, compare with the H1 2023 file by cleaned title only.
- Before the pilot, report the movie/show key collisions: number of keys, share of hours, and the 20 largest by hours, before and after the type is added to the key. Include this in the status note.
- title.akas has about 60 million rows: read it in chunks and keep only rows whose normalised title is in the in-scope key set. Do not load it whole.
- Everything else in this plan, including the pilot stop and the hand check, stays as approved.

Approved: human