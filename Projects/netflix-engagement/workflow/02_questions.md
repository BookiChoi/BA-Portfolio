Author: human
Status: final

# 02 Business Questions

## Q1

### Decision to be made
Content planning and release scheduling leads decide which genres to strengthen in the second-half (Jul–Dec) release and licensing plan, compared with the first half.

### Question
Among genres with an average share of at least 5%, does any genre's share of viewing hours alternate by half-year: moving the same way in every H1-to-H2 transition and the opposite way in every H2-to-H1 transition, by at least 2 percentage points (pp) each time, from H1 2023 to H1 2026?

### Hypothesis
At least one genre shows this alternating pattern, and it holds in all three checks below. The null hypothesis is that no genre passes all three.
1. All labelled titles.
2. Excluding the 10 titles with the most hours in each half-year (seasons of one series count as one title).
3. Separately for titles new to the report in that half-year and titles carried over from the previous half-year (this check covers H2 2023 to H1 2026, five transitions, because H1 2023 has no earlier file).

By chance alone, one genre shows a given alternating pattern across six transitions with probability 2 x (1/2)^6, about 3% (my arithmetic, assuming independent signs; shares sum to 100%, so genres are not independent).

### Metric
- Unit: one genre in one half-year (seven half-years, H1 2023 to H1 2026).
- Genre share = viewing hours of labelled titles in that genre ÷ viewing hours of all labelled titles, per half-year. Unknown titles are excluded from the denominator and reported separately, together with labelling coverage (labelled hours ÷ all hours).
- Shift = share in half-year t+1 minus share in half-year t, in pp, for the six consecutive pairs.
- Genres tested: those with an average share of at least 5%, using 6 to 8 broad genre groups.
- "New" = the cleaned title does not appear in the previous half-year's file; "carried over" = it does. This is not the same as newly released; it also captures licensed titles that entered the report.
- Sensitivity only (not the decision): thresholds of 1.5 pp and 3 pp.
- Genre labels: one primary genre per title from one fixed external source (chosen in step 03), grouped by a mapping table that I write and commit before computing any genre share.

### Data needed
- Netflix "What We Watched" reports for H1 2023, H2 2023, H1 2024, H2 2024, H1 2025, H2 2025 and H1 2026 (seven files). Fields used: title and hours viewed. One row = one title in one half-year (each season of a series is its own row).
- A cleaned title key (strip season, language and year tags) so one show maps to one genre and so titles can be matched across half-years. The match rate and its bias by language are reported in step 03.
- A genre label per title in scope. The labelling scope (top N titles per half-year) is set in step 04 from the cumulative share of hours, before labelling starts.

### Decision rule
- If at least one genre passes all three checks, treat it as a seasonal pattern and use it as a planning assumption: raise that genre's weight in the half-year where it rises, by at most its average observed shift in pp. Record a dated prediction for H2 2026 and score it when Netflix's first annual report (expected Q1 2027) is available, if it allows H2 2026 to be derived.
- If no genre passes, do not plan the genre mix on seasonal shifts; keep the mix of the latest half-year as the baseline.
- This claim describes what was viewed under past slates. It does not say what viewers want, because Netflix's own releases and licensing change the supply.
- The result is reported either way. A null result still tells the planner that genre shares are not seasonally predictable.