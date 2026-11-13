Author: ai/question-coach

# 02 Question feedback: netflix-engagement

Scope: 02_questions.md contains one question (Q1). Feedback below covers Q1 only. I did not read the data files; statements about the data rely on 00_brief.md and 01_research.md, and unverified items are marked.

## Q1: Seasonal H1-to-H2 shift in genre share of viewing hours

### 1. Ambiguity
- "Genre" is not fixed. The mapping table is written later and the source is chosen in step 03, so the question cannot yet be answered or even scoped. The number of broad categories drives the result (see hypothesis test below).
- "Total hours of labelled titles" is the denominator, but the labelled set is "top N titles" with N set in step 04. The share therefore means "share within the labelled top N", not "share of viewing". Say which one you mean, and whether Unknown hours stay in or out of the denominator.
- "Each genre ... in each of 2023, 2024 and 2025": the metric defines a unit of one genre in one year, but the question and hypothesis treat the unit as one genre across three years. Clarify what one observation is.
- "Same direction" (question) versus "same sign and at least 2 pp in each year" (hypothesis). The question is weaker than the rule that tests it.
- "Top 10 titles" are 10 rows, and each season is its own row. One franchise can take several of the 10, so the robustness check may remove a franchise, not 10 titles.
- "Seasonal" is used for what is only an H1/H2 difference. Half-years can differ for reasons that are not seasonal (see assumptions).
- "Held-out" for H1 2026: it was published before the as-of date and is already known, so it is a backtest as you note, not a forecast test. The expected sign also needs stating. H1 2026 minus H2 2025 is an H2-to-H1 move, so "opposite" to the H1-to-H2 shift is the same claim as the pattern, not an independent one.

### 2. Measurability
- The report has no genre column (brief). Everything depends on an external label source and a title-matching step that is not yet chosen or tested. Risk: title strings in the file may not match external catalogs, especially for non-English titles, multi-season titles and titles with alternate names. Matching failures that correlate with language or title type would bias the shares toward English-language genres. Check the Unknown rate by format and language before trusting any share.
- Labelling cost: the research cites a secondary source of 36,121 movie rows over four periods (Cornell project, unverified). Full labelling is not realistic, so top N is needed, but top N creates the selection issue above. Proxy needed: report coverage per half-year and the share of Unknown within the labelled set.
- Primary genre only: a title in several genres is forced into one. Genre shifts could reflect labelling convention rather than viewing.
- Six files across 2023 to 2025 are assumed to exist with comparable layouts. The research lists the H2 2025 page but did not inspect any file, and layout differences across periods are flagged as a risk. Confirm all six exist and what the first covered period is before building on them.
- The 50,000-hour listing threshold is unverified for these files. Small genres could be partly cut off, which matters when the rule uses a 2 pp threshold.
- Hours viewed favour long series over movies, and mix new releases with older catalog. Share of hours is not share of audience or demand.

### 3. Hidden assumptions
- An H1/H2 difference reflects a stable seasonal viewing preference. It more likely reflects what Netflix released and licensed in each half (supply), which is the thing the decision-maker controls. A rising share could mean a big slate, not demand.
- Release timing and right-censoring: titles released late in a half-year have fewer days of viewing (research, section 5). H2 releases in December are cut off by the period end, which could distort H2 shares.
- Three years are enough to call a pattern. Under pure chance, the chance of the same sign in all three years for one genre is 2 x (1/2)^3 = 0.25 (my arithmetic, ignoring the 2 pp rule). With many categories, finding two "consistent" genres is plausible by luck. The 2 pp rule helps, but it is applied equally to genres of very different size: 2 pp is a large move for a genre with a 3% share and a small one for a genre at 25%.
- Shares sum to 100%, so one genre rising forces others down. Consistent genres will tend to come in opposing pairs, which is not independent evidence.
- Membership and catalog size grow over time, and the Netflix title mix changes (licensed versus original, English versus non-English). The shares assume those do not drift across 2023 to 2025.
- The decision link assumes the H2 slate and licensing plan is still adjustable on the basis of last-year patterns. Those plans are typically set well ahead (unverified; this is a domain assumption to check).
- The 2 pp threshold and "top 10" cutoff are asserted without a basis. Neither is tied to observed noise.

### 4. Sharper alternative directions (not wording)
- Benchmark the H1-to-H2 shift against ordinary movement. Compare it with the same genre's change between other adjacent periods (for example H2 to H1, or year over year for the same half) so you can see if H1/H2 is special or just noise.
- Replace a fixed 2 pp cutoff with a relative change or a size-adjusted threshold, and decide up front how many categories you allow (fewer, broader groups).
- Separate supply from demand: compare genre share of hours with genre share of titles listed (or hours per title), for originals versus licensed if the file's availability field allows it (unverified).
- Test a version that needs no external labels first, using fields in the file or easy to derive (movie versus series, runtime band, English versus non-English via the Top 10 filters if usable). This de-risks the dependency and could serve as a fallback.
- Look at the release-cohort view: split each half's hours into titles released in that half versus earlier, so the seasonal story is not confused with release slate.
- Longer view: if the other half-year files are usable, use all available periods (including H1 2026) as data points for the pattern rather than keeping one as held-out, or keep the holdout but state the sign it must show.
- Unused angles from research and brief that could pair with this one: comparing Netflix's own claims against the file (non-English share, new-season effect on earlier seasons); concentration of hours in top titles. These may be stronger portfolio questions because they need no external labels.

### 5. Decision link
- Stated decision: which genres to strengthen in the H2 release and licensing plan. Weak point: the decision-maker is Netflix content planning, and the data can only show what was viewed under past slates. The answer would change the plan only if it separates "H2 viewers prefer genre X" from "Netflix released more X in H2".
- The decision rule is clear in structure (two or more consistent genres versus fewer), but the fallback ("use the most recent half-year mix") is not an alternative decision with its own cost. Say what action differs between the two outcomes and by how much.
- A null result is a likely outcome given the three-year, two-pp, two-test rule. Check that a null still teaches something (for example, "shares are stable, plan from latest mix") and is worth a portfolio chapter.

## Top 3 issues to fix first
1. Supply versus demand: H1/H2 share shifts mostly reflect what was released and licensed, and release timing cuts off late-half titles. Decide how the question separates these, or narrow the claim.
2. Unresolved genre labelling: no genre column, source not chosen, top N undefined, Unknown handling and matching bias unmeasured. The denominator ("labelled top N") changes what the share means. Decide the denominator and test the match rate on a small sample before locking the question.
3. Weak hypothesis test: the same-sign-in-3-years rule passes by chance at 0.25 per genre, the fixed 2 pp threshold ignores genre size, and shares are mutually dependent. Define a benchmark for normal movement and the number of categories before looking at results.

Other items to tidy: align the question wording with the hypothesis rule, fix what "top 10 titles" means given season rows, and state the sign expected for the H1 2026 check.
