Author: ai/researcher
Overall verdict: GO

# 03 Data plan: Netflix engagement (as-of 2026-11-12)

Method note: I did not download any file in this step. Field names below come from secondary sources and are marked "to confirm at profiling". The Netflix H1 2026 page fetch timed out in this step, so nothing new was confirmed from it; claims rely on 01_research.md and the sources linked here.

## Scope
Only Q1 is in 02_questions.md. The verdict is GO conditional on the items in "Conditions" below. These are not blockers for step 04, but they must be settled in step 03/04 before any genre share is computed.

## Q1: data check

| Need (from Q1) | Source | License / terms | Size | Field(s) | Status |
|---|---|---|---|---|---|
| Seven half-year reports, H1 2023 to H1 2026 | Netflix What We Watched xlsx files. H1 2026: [xlsx](https://assets.ctfassets.net/4cd45et68cgf/40WGcHJa9vRua31kU6Gbz5/43b15c7fbd6924392fc80e885839e39f/Netflix-s_What_We_Watched_Report_2026Jan-Jun__1_.xlsx). Other six: linked from each Netflix report page (H2 2025 page: [link](https://about.netflix.com/news/what-we-watched-the-second-half-of-2025)) | No license stated; raw files are not redistributed (brief). Only aggregates are shared | First report: about 18,000 titles, about 99% of viewing ([Axios, 2023-12-13](https://www.axios.com/2023/12/13/netflix-releases-viewing-data-tv-shows-movies-first-time); search summary). Later sizes: unknown until profiled | Title, hours viewed (names to confirm). Press says each row also has premiere date and availability | H1 2023 existence confirmed by press (first report, Dec 2023, covering Jan-Jun 2023). Direct file links for the other five older halves not confirmed here |
| Title key to link titles across halves | Derived from Title | n/a | n/a | Title text only | Feasible; match rate cannot be known until profiled. Season, language and year tags are in the title string per your Q1 wording; not checked |
| Genre label per title | External source, not in the Netflix files (brief states no genre column) | See candidates below | Per title lookup for the top N titles | Genre | Source not yet chosen; this is the main dependency |
| Hours-weighted shares | Same files | n/a | n/a | Hours viewed | Feasible if each half has hours for each title |

Field-by-field verdict for the fields Q1 names:
- Title: exists per press descriptions and TidyTuesday `title`. To confirm in each xlsx.
- Hours viewed: exists (TidyTuesday `hours_viewed`; press confirms hours per title). To confirm in each xlsx.
- Genre: does NOT exist in the Netflix files. Needs an external source.
- Season (for "seasons of one series count as one title"): no separate field is documented; it must be parsed from the title text. Risk: inconsistent title formats.
- Release date is not required by Q1. The "new vs carried over" test uses presence in the previous file, not release date.

## Genre source candidates (decision belongs to the human)
| Candidate | Terms | Fit | Caveats |
|---|---|---|---|
| TMDB API | Free for non-commercial use with attribution notice in an About/Credits section; commercial use needs a license ([TMDB FAQ](https://developer.themoviedb.org/docs/faq)). The FAQ page I fetched did not mention genre fields or rate limits; confirm in the API docs | Covers movies and TV, and has its own genre lists (from my general knowledge, UNVERIFIED here) | Title search matching is fuzzy; TMDB lists multiple genres per title, so a "primary genre" rule is needed and must be written before labelling. Portfolio use is likely non-commercial; confirm |
| IMDb datasets / OMDb | Not checked in this step | Unknown | Not verified; check terms before choosing |
| Manual labelling of top N titles | Own work | Full control, no license issue | Slow; reproducibility depends on the committed mapping |

## Other TidyTuesday data (candidate C)
[TidyTuesday 2025-07-29](https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-07-29) covers only H2 2023 to H1 2025 (four files), with columns source, report, title, available_globally, release_date, hours_viewed, runtime, views. It lacks H1 2023, H2 2025 and H1 2026 and has no stated license on the page, so it cannot replace the Netflix files. It can serve only as a cross-check of the parsing.

## Per-question verdict
| Question | Verdict | Reasons | Risks |
|---|---|---|---|
| Q1 | GO (conditional) | Netflix title and hours data exist for all seven halves according to press and the research step; genre can be added from an external source; all three checks (all titles, excluding top 10, new vs carried over) need only title and hours plus the title key and genre | See below |

## Conditions to meet before computing any genre share
1. Download and profile all seven files. Confirm each exists, the column names, row counts, and whether the layout is the same across halves. The file for each half must be retrievable; record URL, date and rows in `data_manifest.json`.
2. Choose one genre source and write the mapping table (6 to 8 groups) before any share is computed, as Q1 requires.
3. Fix a primary-genre rule for multi-genre sources.
4. Set the labelling scope in step 04 from cumulative hours share; report labelling coverage (labelled hours / all hours).

## Risks
- Genre labelling coverage may be low or biased. Non-English and licensed titles are harder to match by name, so genre shares may be biased by language. Q1 already requires reporting match rate and bias.
- Right-censoring and supply effects: shares reflect Netflix's own release slate, not viewer demand (Q1 notes this).
- 50,000-hour threshold: titles below it are not listed, so shares are among listed titles only. Whether the threshold applies identically across halves is unverified.
- Title duplicates or renamed titles across halves can distort "new vs carried over".
- Statistical power: seven half-years give six transitions per genre. With 6 to 8 genres tested, the chance that some genre passes by luck is higher than the 3% your arithmetic gives for one genre (2 x (1/2)^6 = 2/64, about 3.1%). The 2 pp threshold is the main guard. This is a note, not a change to the question.
- Source continuity: Netflix says it moves to a yearly snapshot from Q1 2027 ([H1 2026 report](http://about.netflix.com/en/news/what-we-watched-the-first-half-of-2026), per 01_research.md). Whether H2 2026 can be derived from that report is unknown, so the dated H2 2026 prediction may not be scorable.
- Weekly Top 10 is not required by Q1 and is not used.

## Blockers
None found. If step 03/04 profiling shows that any of the seven files is unavailable, or that no genre source reaches usable coverage for the top N titles, the verdict for Q1 changes to NO-GO.

## Human decisions at Gate 1 (2026-11-12)
- All seven report files are in hand (verified by the data profile in 01b). Source URLs and download dates are recorded in data_manifest.json.
- Genre source: TMDB, used under its non-commercial terms with the required attribution. No ads or monetisation on any page that shows this work. Approved endpoints: TMDB search, details and genre-list endpoints for movies and TV (the analyst lists the exact URLs in the analysis plan). IMDb/OMDb are not approved.
- Primary genre: assigned by a priority-ordered mapping table that I write and commit before any genre share is computed. "First listed genre" is not used.
- Pilot: label 30 titles (English and non-English) and report the match rate before full labelling. If the match rate is below 85%, revise the matching method first.
- Coverage rule: if unlabelled titles exceed 10% of a half-year's viewing hours within the labelled scope, Q1 is reported as inconclusive.
- Multiple testing: the analysis plan must estimate the chance of a spurious pass across all tested genres (for example by permutation). Any pass is reported as a lead to re-check, and genres that move as a pair count as one finding.
- API keys stay outside the repository and are never pasted into files or chat.

## Amendment to Gate 1 (2026-11-12)
- Genre source changed from TMDB to the IMDb Non-Commercial Datasets (title.basics.tsv.gz and title.ratings.tsv.gz, optionally title.akas.tsv.gz if the plan justifies it). No API key or account is needed. The files stay outside the repository; the download date and sha256 go in data_manifest.json.
- TMDB is not used. Earlier references to TMDB keys and endpoints no longer apply.
- Use is personal and non-commercial; no raw IMDb data is published, only aggregates. Attribution follows the IMDb terms, which I have read.
- Matching must be written down before the pilot and measured: title type, release year and a tie-break rule (for example most votes). Report the match rate and a hand check of the pilot titles.
- The genre mapping is by IMDb genre names (up to three per title) with the priority table, as before.
- Requests for the new analysis plan: keep the Gate 1 pilot (30 titles, 85%) and coverage (10%) rules; handle H1 2023, which has no movie/show split; cap the labelling scope (stop and ask if unique title keys exceed 3,000); report the pair rule (r <= -0.9) before and after; define the language rule for unmatched titles by the " // " tag.

Approved: human