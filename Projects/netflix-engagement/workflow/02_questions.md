Author: human
Status: ready-for-coach

# 02 Business Questions

## Q1

### Decision to be made
Content planning and release scheduling leads decide which genres to strengthen in the second-half (Jul–Dec) release and licensing plan, compared with the first half.

### Question
Does each genre's share of viewing hours (genre hours ÷ total hours of labelled titles in that half-year) shift in the same direction from H1 to H2 in each of 2023, 2024 and 2025?

### Hypothesis
At least two genres show a consistent H1-to-H2 shift: the same sign in all three years, with an absolute change of at least 2 percentage points (pp) in each year, both with and without the top 10 titles. The null hypothesis is that fewer than two genres meet this rule.

### Metric
- Unit: one genre in one year (2023, 2024, 2025).
- Genre share = viewing hours of labelled titles in that genre ÷ viewing hours of all labelled titles, per half-year. Labelling coverage (labelled hours ÷ all hours of the half-year) is reported alongside.
- Seasonal shift = H2 share minus H1 share of the same year, in percentage points.
- "Consistent" = same sign in all three years and an absolute shift of at least 2 pp in each year.
- Main result: all titles included. Robustness check: exclude the 10 rows with the most viewing hours in each half-year. A genre counts as consistent only if it passes both.
- Genre labels: one primary genre per title from one fixed external source (chosen in step 03), grouped into broad categories by a mapping table I write before looking at results.

### Data needed
- Netflix "What We Watched" reports for H1 and H2 of 2023, 2024 and 2025 (six files): title and hours viewed. One row = one title in one half-year (each season of a series is its own row).
- The H1 2026 report as a held-out check: not used to define the pattern. Afterwards I check whether the H2 2025 to H1 2026 change runs in the opposite direction for the consistent genres. It is already published, so this is a backtest.
- A genre label for each title in scope from one external source, plus a title-cleaning rule (strip season, language and year tags) so that one show maps to one genre. Titles that cannot be matched are labelled "Unknown" and reported.
- The labelling scope (top N titles per half-year) is set in step 04 from the cumulative share of hours.

### Decision rule
- If at least two genres are consistent (with and without the top 10 titles), treat them as a seasonal pattern and use them as a starting point for the H2 slate and licensing plan, re-checked each year.
- If fewer than two genres are consistent, do not plan the H2 genre mix on seasonal shifts; use the most recent half-year mix as the baseline.
- The held-out H1 2026 check is reported either way and does not change this rule.