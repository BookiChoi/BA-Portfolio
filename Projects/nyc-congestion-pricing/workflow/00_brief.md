Author: human
Status: final

# 00 Brief

## Chosen company and why
NYC TLC trip record data. I chose it for two reasons: it is recent (monthly files up to
September 2026), and it records real trips that people actually took, so I expect it to
show how people move around the city.

## What I found myself (links and notes)
- TLC Trip Record Data page: files are published monthly, latest is September 2026.
  https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Data dictionaries (yellow, green, FHV, high-volume FHV) and the Trip Record User Guide
  are linked from the same page.
- Claude read the yellow and high-volume FHV dictionaries for me and reported that both
  contain a cbd_congestion_fee field (Congestion Relief Zone, from 2025-01-05).
  I have not opened these PDFs myself yet.
- I did not find a license or terms-of-use statement on the pages I looked at.

## What I am initially curious about
1. Which areas have the most trips, and which origin-to-destination pairs are the most common?
2. Beyond those top areas, is there a reason to put effort into the rest (a Pareto-style question)?
3. Does usage differ between weekdays and weekends?
4. Are there "blue ocean" areas, meaning places that look underserved?

## Constraints
- Files are large (monthly Parquet); one month may be heavy to process locally.
- Raw data stays outside the repo; only aggregated results are published.
- No license statement found (checked 2026-11-13). To be recorded in the data manifest.
- Dictionaries are dated March 2025; real column names must be checked in the actual files.
- Not yet decided: which services to use (yellow taxi, high-volume FHV such as Uber/Lyft, or both).
- Scope: I want to look at three views separately: yellow taxi only, high-volume FHV
  (Uber/Lyft) only, and both combined. Green taxi and other FHV files are not planned.

---
Draft prepared with AI help (Claude); I reviewed and edited it.