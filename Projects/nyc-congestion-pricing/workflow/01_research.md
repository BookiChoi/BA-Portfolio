Author: ai/researcher

# 01 Research: NYC TLC trip records and congestion pricing

Research date: 2026-11-13. Input: `00_brief.md` only. No business questions are proposed here.

## 1. Organization context
- Publisher: NYC Taxi and Limousine Commission (TLC). The TLC page states the trip data was collected by technology providers (TPEP/LPEP for yellow taxi; licensed bases for for-hire vehicles), not created by TLC, and TLC makes no accuracy representations. Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page (fetched 2026-11-13).
- High-volume FHV (HVFHV, e.g. Uber/Lyft) is published as its own, more detailed dataset (same page).
- Per the page, publication lag is about two months; latest listed month for both yellow and HVFHV is September 2026 (same page; matches the brief).
- Data is also mirrored on NYC Open Data (same page) and the AWS Open Data registry: https://registry.opendata.aws/nyc-tlc-trip-records-pds/

## 2. Recent news (paraphrased, MTA/state sources are interested parties)
- 2026-01-05: The MTA and Governor Hochul reported first-year results of the Congestion Relief Zone toll: about 27 million fewer vehicles entering the zone (about 11% less traffic), faster crossing speeds, and over $550M raised for transit. Sources: https://www.governor.ny.gov/news/less-traffic-better-transit-its-first-anniversary-governor-hochul-celebrates-transformational ; https://politicsny.com/2026/01/05/congestion-pricing-27-million-fewer-vehicles-entered-manhattans-central-business-district-in-first-year-of-toll-program-mta-says/
- Same period: reported subway/bus ridership entering the zone rose (about 9% subway), per the MTA press release: https://www.mta.info/press-release/icymi-less-traffic-better-transit-its-first-anniversary-governor-hochul-celebrates
- Reported side effects/critiques: more complaints about illegal parking outside the zone, and a Town of Hempstead lawsuit challenging the fees. Summary article: https://abc7ny.com/post/nyc-congestion-pricing-results-year-later-has-toll-been-success/18331318/
- Caveat: I only saw search-result summaries of these articles, not full text; figures should be re-checked at the linked pages before being quoted in the project. I found no later-2026 results.

## 3. Industry background
- Congestion pricing: a per-vehicle charge for entering Manhattan's central business district, started 2025-01-05 (date per brief; dictionary field `cbd_congestion_fee`). Base passenger-car toll reported as $9 (ABC7 link above). Taxi and FHV trips are charged a per-trip fee that appears in the TLC files (field name below, unverified).
- Trip records are a standard open dataset for urban mobility analysis; the yellow taxi vs app-based FHV split matters because FHV volume and fee structures differ (HVFHV carries more detailed fields).
- No independent (non-government) evaluation was found in this pass; a later search is advisable if the analysis cites policy effects.

## 4. Candidate datasets

### A. Yellow taxi trip records
- URL pattern: `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet` (from TLC page).
- Dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf
- Format: monthly Parquet. Size: NOT VERIFIED (no HEAD/download done; to be recorded in `data_manifest.json` with row count at download).
- Fields: UNVERIFIED. The PDF could not be read in this session (WebFetch returned binary; PDF rendering needs `pdftoppm`, not installed). The TLC page states 2025+ files include `cbd_congestion_fee`. Pickup/dropoff location IDs, datetimes, fares are expected from general knowledge but must be confirmed in the real Parquet schema.
- Caveats: dictionary dated March 2025 (brief); schema may be standardized across years in future (TLC page); records come from providers and may contain errors, so outliers (zero/negative fares, odd dates) are likely.

### B. High-volume FHV (Uber/Lyft) trip records
- URL pattern: `https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_YYYY-MM.parquet`.
- Dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf
- Format: monthly Parquet. Size: NOT VERIFIED; HVFHV months are expected to be much larger than yellow (general expectation, unmeasured), so local processing needs column pruning or chunking.
- Fields: UNVERIFIED for same reason; TLC page states `cbd_congestion_fee` exists from 2025.
- Caveats: as above; combining with yellow requires harmonizing column names and fare semantics.

### C. Taxi zone lookup and shapefile
- Linked from the TLC trip record page (taxi zone lookup CSV and zone shapefile; exact URLs not extracted in this pass, the last ~3k characters of the page were not read). Needed to map location IDs to borough/zone and to flag Congestion Relief Zone areas. Fields not verified.

### D. Supporting documents
- Trip Record User Guide: https://www.nyc.gov/assets/tlc/downloads/pdf/trip_record_user_guide.pdf
- Working with Parquet guide: https://www.nyc.gov/assets/tlc/downloads/pdf/working_parquet_format.pdf

## 5. License status
- No license or terms-of-use text on the TLC page (WebFetch of the page, 2026-11-13); consistent with the brief.
- AWS registry lists the NYC.gov Terms of Use as the license: https://registry.opendata.aws/nyc-tlc-trip-records-pds/ ; terms page: https://www.nyc.gov/html/data/terms.html (full text not retrieved; permissions unverified).
- NYC Open Data users agree to NYC.gov terms plus any agency-specific terms (search summary).
- Recommendation for manifest: record "no explicit license on TLC page; NYC.gov Terms of Use referenced by AWS registry; read the terms page before publishing."

## 6. Blockers and open items
1. Both data dictionaries were unreadable here, so field lists and the exact `cbd_congestion_fee` presence are unconfirmed by me (the brief's claim was also unverified by the human). Resolve by reading the real Parquet schema (`pyarrow` schema read, no full download needed) in the feasibility stage.
2. File sizes and row counts not measured.
3. NYC.gov Terms of Use full text not read.
4. Taxi zone lookup URLs not extracted.
