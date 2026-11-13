Author: ai/researcher

# 01 Research: Netflix engagement (as-of 2026-11-12)

Method note: facts come from fetched pages or search summaries, paraphrased. Items marked UNVERIFIED were not confirmed from a primary source in this step. I did not download the xlsx, so file-level facts (columns, row counts, missing rates) are still to be checked in step 03.

## 1. Company context and business model
- Revenue comes mainly from membership fees, with an ad-supported tier growing. Coverage of the Q1 2026 shareholder letter says growth came from membership growth, pricing and ad revenue ([Subscription Insider](https://www.subscriptioninsider.com/article-type/news/netflix-says-ad-supported-tier-reaches-250m-monthly-active-viewers-as-membership-fees-still-drive-revenue)).
- Ad tier (May 2026 Upfront, per press): reported at more than 250M monthly active viewers, up from 190M in Nov 2025; expansion to 15 more countries; 2026 revenue guidance of $50.7B to $51.7B, with ad revenue expected to roughly double ([Engadget](https://engadget.com/2172449/netflixs-ad-tier-now-has-a-whopping-250-million-monthly-users), [TheWrap](https://www.thewrap.com/media-platforms/streaming/netflix-ad-tier-monthly-active-viewers-update-upfronts-2026/)).
- Metric caveat: "monthly active viewers" counts a household member who watched at least one minute of ad content, scaled by estimated household size. It is a reach measure, not paid accounts. Earlier figures counted profiles.
- Subscriber reporting: the search did not confirm whether Netflix still reports quarterly subscriber counts. UNVERIFIED. Check a Netflix shareholder letter on ir.netflix.net.
- Engagement report cadence: What We Watched is half-yearly. Netflix says it moves to a yearly snapshot starting Q1 2027 ([Netflix, H1 2026 report](http://about.netflix.com/en/news/what-we-watched-the-first-half-of-2026)). So H1 2026 may be the last half-year file.

## 2. Recent news: H1 2026 report (Netflix, accessed 2026-11-12)
Source: [What We Watched, first half of 2026](http://about.netflix.com/en/news/what-we-watched-the-first-half-of-2026). Netflix's own claims, not yet checked against the file:
- Over 97B hours viewed in Jan-Jun 2026, described as the highest half-year total reported.
- Most-watched show His & Hers, 104M views; biggest title War Machine, 147M views.
- Bridgerton S4 100M views; franchise 180M.
- Non-English more than a third of viewing; more than half of members watched at least one anime title; Ms. Rachel top kids title at 69M views; India at a record half-year.
- Full file: [xlsx](https://assets.ctfassets.net/4cd45et68cgf/40WGcHJa9vRua31kU6Gbz5/43b15c7fbd6924392fc80e885839e39f/Netflix-s_What_We_Watched_Report_2026Jan-Jun__1_.xlsx).
- The page text I retrieved did not state the live-event numbers (Kevin Hart 21M, Skyscraper Live 13M, BTS 21M) from your brief; they were not confirmed here. The fetch tool summarizes pages and may omit sections.

## 3. What Netflix analysts work on (job postings)
The search found mostly "Analytics Engineer" roles (L4/L5), via aggregators that may be stale. Not found: a role titled "Data Analyst". Check the Netflix careers site for live postings.
1. Analytics Engineer 5, Member Insights Engineering: explore trends in member engagement to find opportunities ([Working Nomads](https://www.workingnomads.com/jobs/analytics-engineer-4-member-insights-engineering-netflix-1519249) lists the L4 version; L5 at [Rise](https://joinrise.co/netflix/analytics-engineer-5-member-insights-engineering-3dy9)).
2. Analytics Engineer 5, Content: measurement insights, data products and prototypes informing content decisions; expects 5+ years, expert SQL, Python or R ([Dice](https://www.dice.com/job-detail/a5cd5c6e-dd4a-4ef0-9462-da3d29ca8540)).
3. Analytics Engineer 5, Ads Revenue Analytics: build a unified revenue analytics narrative for the Ads business ([Working Nomads](https://www.workingnomads.com/jobs/analytics-engineer-5-ads-revenue-analytics-netflix-1533568)).
Common skills in the summaries: SQL, Python, ETL/warehouse basics, Tableau-style visualization. I did not open each posting; salary figures conflicted across listings and are omitted.

## 4. How others analysed What We Watched
- TidyTuesday 2025-07-29 release (curated by Jen Richmond; Netflix reports late 2023 to H1 2025) ([GitHub](https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-07-29), [example write-up](https://seanthimons.github.io/posts/2025-07-29-what-have-we-been-watching-on-netflix/2025-07-29-what-have-we-been-watching-on-netflix.html)).
- Cornell student projects: global vs regional titles ([1](https://pages.github.coecis.cornell.edu/info3312-sp26/proj-01-proud-mink/presentation.html)); release season vs views ([2](https://pages.github.coecis.cornell.edu/info3312-sp26/proj-01-proud-beaver/presentation.html)).
- Press/blog: [DTVE long-tail analysis](https://digitaltveurope.com/longread/dtve-data-weekly-analysing-the-long-tail-of-netflix-viewing), [Stat Significant](https://stat-significant.beehiiv.com/p/watched-netflix-2023-statistical-analysis), [Carta on storytelling](https://carta.com/data/linkedin-netflix-data-engagement-report-storytelling/).
- Angles that look less covered (observations, not questions): tracking the same title across several half-years (decay, season effects); concentration of viewing in the top titles; comparing Netflix's own claims against the file; Top 10 weekly vs half-year totals. This is based on a limited search, so "unexplored" is a hypothesis.

## 5. Definitions and limits
- Views = hours viewed divided by runtime (Netflix reports; TidyTuesday readme says `views` is derived). Top 10 page shows views, runtime and hours but does not define them ([Tudum Top 10](https://www.netflix.com/tudum/top10)).
- Hours viewed: total time watched per title in the period. Netflix says the reports cover about 99% of viewing (via TidyTuesday readme, for H1 2025).
- 50,000-hour threshold: not defined on the H1 2026 page I retrieved. From your brief and secondary sources: titles below it are not listed. UNVERIFIED for H1 2026; look for a notes/readme sheet in the xlsx.
- Release date: secondary sources report roughly 80% missing in earlier files (Cornell/search summary); check in the H1 2026 file.
- Titles can appear in multiple periods, so period comparisons need care. Aggregated by title; no user-level, genre or language fields per the brief.
- Right-censoring risk: titles released late in the half-year have fewer days of viewing.

## 6. Weekly Top 10 usability
- Source: [Tudum Top 10](https://www.netflix.com/tudum/top10). Weekly lists from the week of 2021-06-28 through the week 2026-11-02 to 11-08. Fields shown: rank, title, views, runtime, hours viewed. Filters: country, movies/shows, English/non-English.
- No download button was visible on the page. Terms of use are only linked, not summarized. Whether a downloadable file exists, and under what terms, is UNVERIFIED; check the Terms of Use and any "download" link in a browser before relying on it. Scraping may be restricted.
- Data after 2026-11-12 may only be used for scoring predictions.

## 7. Candidate datasets
| # | Dataset | Source | License | Size | Fields | Caveats |
|---|---|---|---|---|---|---|
| A | H1 2026 What We Watched xlsx | [link](https://assets.ctfassets.net/4cd45et68cgf/40WGcHJa9vRua31kU6Gbz5/43b15c7fbd6924392fc80e885839e39f/Netflix-s_What_We_Watched_Report_2026Jan-Jun__1_.xlsx) | Not stated; do not redistribute, per brief | Not inspected | Expected: title, release date, runtime, hours, views, availability (to verify) | Raw file not to be committed; 50k threshold |
| B | Earlier Netflix reports (2023-2025 halves) | [Netflix report page, H2 2025](https://about.netflix.com/news/what-we-watched-the-second-half-of-2025) and linked files | Not stated | Not inspected | Same layout presumably | Layout may differ across periods |
| C | TidyTuesday 2025-07-29 `movies.csv`, `shows.csv` | [GitHub](https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-07-29) | Not stated on page (repo-level license UNVERIFIED) | Not stated. Secondary source: 36,121 movie rows over four periods (Cornell project) | source, report, title, available_globally, release_date, hours_viewed, runtime, views | Ends H1 2025; "Available Globally?" artifact rows reported; derived `views` |
| D | Weekly Top 10 | [Tudum](https://www.netflix.com/tudum/top10) | Terms link only | Weekly since 2021-06-28 | rank, title, views, runtime, hours | No confirmed download |

Combining A, B and C would give several half-years for the same titles; only A and B are primary sources.

## 8. Open items for step 03
Download and profile A (columns, rows, release-date missing rate, threshold note); confirm B files exist for each half-year; confirm Top 10 download and terms; confirm subscriber-reporting status.
