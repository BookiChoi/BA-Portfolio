Author: ai/researcher
Overall verdict: GO

# 03 Data Plan: feasibility check for Q1-Q4

Date: 2026-11-13. Inputs: `00_brief.md`, `01_research.md`, `02_questions.md`. Questions are not changed.

Tool limits in this session: no shell, so I could not download Parquet files, read their schema, or count rows. The TLC dictionaries are PDFs that came back as binary (a saved copy could not be rendered because `pdftoppm` is missing). So the GO below is conditional on one schema check (section 5, step 1). Items I could not verify are marked UNVERIFIED.

## 1. Sources

| Source | URL | Status |
|---|---|---|
| Yellow taxi monthly Parquet | `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet` | URL pattern from TLC page; files not opened |
| HVFHV monthly Parquet | `https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_YYYY-MM.parquet` | same |
| Taxi zone lookup CSV | https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv | URL confirmed on TLC page (fetched 2026-11-13); contents not opened |
| Taxi zone shapefile | https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip | URL confirmed on TLC page |
| MTA "Central Business District Taxi Zones" (data.ny.gov, dataset id `yfdc-w5jh` per search result) | listed at https://catalog-beta.data.gov/dataset/mta-central-business-district-taxi-zones | Search snippet says it maps TLC zones to the CBD, last modified 2024-09-04. The catalog page itself returned 404 when fetched, so the snippet is unconfirmed. |
| TLC page | https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page | Fetched; the last ~3k characters (2009 section) were not read, which does not affect 2023-2026 |

Needed months: Jan-Sep for 2023, 2024, 2025, 2026 (Q4; Q1-Q3 can use a subset) = 36 files per service, 72 files total. The brief and TLC page say the latest month is September 2026, so Jan-Sep 2026 should exist (not re-verified by file request).

## 2. License
- The TLC page has no license or terms text, only accuracy disclaimers (page fetch, 2026-11-13). Quote: the TLC "makes no representations as to the accuracy" of yellow/green data and cannot guarantee FHV completeness.
- AWS registry lists NYC.gov Terms of Use (per 01_research). The terms URL in 01 (`https://www.nyc.gov/html/data/terms.html`) returned HTTP 404 today, so the terms text is still UNREAD.
- Risk: low for publishing aggregates only, but the manifest must say "no explicit license on TLC page; terms not retrieved". Raw data stays out of the repo (matches the CLAUDE.md data rules).

## 3. Size
- Per-file size and row counts: UNVERIFIED. Nothing on the TLC page lists them. I found only a third-party figure of about 1.5B rows for the whole rideshare table (https://docs.delphina.ai/sandbox/nyc-taxi-rideshare, not official, no per-month breakdown). Record exact sizes and row counts in `data_manifest.json` at download.
- Expectation (not measured): HVFHV months are much larger than yellow. 36 HVFHV files is the main compute risk. Mitigation: read only the needed columns with pyarrow, aggregate one file at a time, and keep only the aggregates. The Q2 note about reducing months is allowed by 02 ("period may be reduced after file sizes are known").

## 4. Field check per question

Column names below come from my general knowledge of the TLC schemas and are UNVERIFIED unless marked. The only field confirmed by an official page is `cbd_congestion_fee`: the TLC page says it was added to the Yellow, Green and HVFHV datasets "for 2025 data onwards" (page fetch, 2026-11-13). This agrees with the brief, but the brief's claim came from the same unread dictionaries.

| Needed concept | Yellow field (expected) | HVFHV field (expected) | Verified |
|---|---|---|---|
| Pickup datetime | `tpep_pickup_datetime` | `pickup_datetime` | No |
| Dropoff datetime | `tpep_dropoff_datetime` | `dropoff_datetime` | No |
| Pickup zone | `PULocationID` | `PULocationID` | No (name used in 02 itself) |
| Dropoff zone | `DOLocationID` | `DOLocationID` | No |
| CBD fee | `cbd_congestion_fee` | `cbd_congestion_fee` | Yes, existence on 2025+ files per TLC page; exact dtype not seen |
| Zone name, borough | `Zone`, `Borough`, `LocationID` in lookup CSV (expected) | same | No |

### Q1 (top pickup zones by day-part, concentration)
- Needs: pickup datetime, `PULocationID`, zone lookup (airport names). One row = one trip (assumed for both services; TLC page describes each record as a trip, but the exact statement was not checked).
- Verdict: GO. Risks: zone IDs 264/265 (unknown/outside) must be excluded and counted, as 02 requires (ID meaning UNVERIFIED, check in lookup). The airport list must be fixed from the lookup before results (expected JFK, LaGuardia, and possibly Newark; confirm names). Month-stability check needs at least a few months per service.
- Note: pickup-only, so the volume is small to extract; HVFHV time is the cost.

### Q2 (airport-origin destinations)
- Needs: Q1 fields plus `DOLocationID`.
- Verdict: GO. Risks: the top-5 share comparison depends on the Q1 top-5 definition (by service, whole period); HVFHV airport trips are a small slice, so counts per destination should be sufficient but are not measured. Newark may exist as a zone with few TLC trips.

### Q3 (weekday vs weekend, night share)
- Needs: pickup datetime only.
- Verdict: GO. Risks: holidays (deferred to 04 by 02); timestamps assumed local time (UNVERIFIED, check in the schema/user guide); stray out-of-range dates in raw files must be filtered to the month of the file (the TLC page warns of provider errors). The Mon-Thu spread rule needs the day-level share, which is derivable from the same field.

### Q4 (CRZ share, 2023/2024 vs 2026)
- Needs: pickup and dropoff zone IDs for 36 files per service, CRZ zone list, `cbd_congestion_fee` for 2025+ cross-check.
- Verdict: GO, with the most risk of the four:
  1. CRZ zone membership must be fixed from an official source before results. Candidate: the MTA CBD taxi zones dataset (above). The official boundary is Manhattan at and south of 60th Street, excluding FDR Drive, West Side Highway and Hugh L. Carey Tunnel connections to West Street (MTA material via search result, https://mta.info/document/131571; not opened). Taxi zones do not match this boundary exactly, so edge zones need a stated rule.
  2. Zone ID stability across years is UNVERIFIED. The TLC page mentions no change; 02 already requires checking it.
  3. The TLC page warns that the Parquet schema may be standardized "in the near future", so re-read the schema at download time and record the download date.
  4. `cbd_congestion_fee` cross-check applies only after 2025-01-05; January 2025 files include trips before that date, which is fine for the 2024 and 2026 comparison but should be handled for the fee check.
  5. There is no 2025 data in the comparison (2024 vs 2026), but 2025 files can serve as an extra check on the fee field. It is optional.
  6. The 2023 to 2024 drift baseline is a single year-to-year comparison; its weakness is limited power, not a data issue.

## 5. Open items and next steps (for 04, before any analysis)
1. Schema check (blocking for any result): read the Parquet schema of one yellow and one HVFHV file (2024-01 and 2026-01) with `pyarrow` and confirm the field names in section 4, plus dtypes and timezone handling. If a name differs, update the plan only (questions are unchanged). If `cbd_congestion_fee` or any location ID field is absent, this verdict becomes NO-GO for the affected question.
2. Record per-file size, row count, download date and source URL in `data_manifest.json`.
3. Download and read the zone lookup; fix airport zones and CRZ zones in writing before results.
4. Locate the working NYC.gov terms text, since the URL in 01 returned 404 today.
5. Size decision: time one HVFHV month with column pruning before committing to all 36 months.

## 6. Verdict summary

| Question | Verdict | Main reason / risk |
|---|---|---|
| Q1 | GO | Pickup time and `PULocationID`; fix airport list first |
| Q2 | GO | Adds `DOLocationID`; depends on the Q1 top-5 definition |
| Q3 | GO | Pickup time only; holidays and timestamps to settle in 04 |
| Q4 | GO (conditional) | CRZ zone list, zone ID stability, and 36 files per service are unverified |
| Overall | GO | Conditional on the schema check in step 1; nothing found that is missing, but field names and sizes were not directly verified |

## Human decisions at Gate 1 (2026-11-13)
Author of this block: human. The text above is unchanged.

1. Data acquisition. I downloaded the files myself into data/ (not committed).
   60 parquet files: yellow and fhvhv, Jan-Sep 2023, Jan-Sep 2024, Oct-Dec 2025,
   Jan-Sep 2026, plus taxi_zone_lookup.csv. The analyst does not download anything.
2. Schema check (done by me on the 2024-01 and 2026-01 files of each service).
   Confirmed: pickup/dropoff datetime, PULocationID, DOLocationID in both services.
   cbd_congestion_fee is present in the 2026 files and absent in the 2024 files.
   HVFHV also has request_datetime and on_scene_datetime (not used by Q1-Q4).
   Not yet checked: the other 56 files. The analyst checks the schema of all files
   (metadata only) in the 04 plan.
3. Size (sample months). Yellow: about 3.0-3.7 million rows, 48-61 MB per month.
   HVFHV: about 19.7-20.9 million rows, 451-482 MB per month.
4. Terms of use. not found, checked 2026-11-13
5. Zone lists. Airport zones for Q1 and Q2: LocationID 1 (Newark Airport), 132 (JFK
   Airport), 138 (LaGuardia Airport), from the "airport" search in taxi_zone_lookup.csv.
   Congestion Relief Zone for Q4: the zone IDs in the MTA Central Business District Taxi
   Zones file (38 rows). Both lists are saved as files in the project before any result
   is computed. Edge-zone rules are set in the 04 plan.
6. Analysis period: as in 02 (Q1-Q3: Oct 2025 - Sep 2026; Q4: Jan-Sep 2023, 2024, 2026).
7. Verdict. I accept GO. The schema condition is met for the sample files (item 2).

Approved: human