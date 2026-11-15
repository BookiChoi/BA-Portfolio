"""Step 1: schema/metadata check of all 60 Parquet files + manifest.

Run from the project folder: python -m pipeline.run_step1
"""
from collections import defaultdict

import pandas as pd

from . import config as C, load as L


def main():
    recs = [L.inspect_file(s, ym) for s in C.SERVICES for ym in C.ALL_MONTHS]
    print("files inspected:", len(recs), "per service:", {s: sum(r["service"] == s for r in recs) for s in C.SERVICES})

    need = {"yellow": ("tpep_pickup_datetime", "tpep_dropoff_datetime"), "fhvhv": ("pickup_datetime", "dropoff_datetime")}
    rows = []
    for r in recs:
        s = r["service"]; c = r["cols"]
        rows.append({"service": s, "ym": f"{r['year']}-{r['month']:02d}", "rows": r["rows"], "MB": round(r["bytes"] / 1e6, 1),
                     "pickup_dt": c.get(need[s][0]), "dropoff_dt": c.get(need[s][1]),
                     "PULocationID": c.get("PULocationID"), "DOLocationID": c.get("DOLocationID"),
                     "cbd_congestion_fee": c.get("cbd_congestion_fee")})
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_rows", 200, "display.max_columns", 30)
    print(df.to_string(index=False))

    print("\n== distinct required-field dtype signatures ==")
    sig = df.drop(columns=["ym", "rows", "MB"]).fillna("ABSENT")
    for key, g in sig.groupby(list(sig.columns)):
        print(key, "->", len(g), "files")

    print("\n== full column-set signatures ==")
    groups = defaultdict(list)
    for r in recs:
        groups[(r["service"], tuple(r["cols"].items()))].append(f"{r['year']}-{r['month']:02d}")
    for i, ((s, cl), ms) in enumerate(groups.items()):
        print(f"[schema {i}] {s}: {len(ms)} files: {ms[0]}..{ms[-1]} ({','.join(ms) if len(ms) < 12 else 'many'})")
        print("   ", dict(cl))

    print("\n== month row counts vs service median (flag > 30%) ==")
    for s in C.SERVICES:
        d = df[df.service == s]; med = d.rows.median()
        print(s, "median rows", med, "min", d.rows.min(), "max", d.rows.max())
        print("  flagged:", d[(d.rows - med).abs() / med > 0.30][["ym", "rows"]].values.tolist())

    print("\n== stop-condition checks ==")
    for s in C.SERVICES:
        d = df[df.service == s]
        print(s, "n files", len(d), "(30 expected); zero-row files:", int((d.rows == 0).sum()))
        print(s, "missing pickup dt:", int(d.pickup_dt.isna().sum()), "missing PU:", int(d.PULocationID.isna().sum()),
              "missing DO:", int(d.DOLocationID.isna().sum()))
        fee = d[d.ym >= "2025-10"]
        print(s, "cbd_congestion_fee missing in Oct25-Sep26 files:", int(fee.cbd_congestion_fee.isna().sum()), "of", len(fee))
        print(s, "cbd_congestion_fee present in pre-2025 files:", int(d[d.ym < "2025"].cbd_congestion_fee.notna().sum()))

    entries = []
    for r in recs:
        name = r["path"].name
        entries.append({"name": name, "file_path": f"data/{name}",
                        "source_url": f"{C.BASE_URL}/trip-data/{name}",
                        "license": "no explicit licence on TLC page; terms not found, checked 2026-11-13",
                        "downloaded_on": C.DOWNLOAD_DATE, "row_count": r["rows"],
                        "checksum": {"algorithm": "sha256", "value": L.sha256(r["path"])},
                        "notes": f"size_bytes={r['bytes']}; downloaded by the human (03_data_plan gate 1)"})
    for p, url, note in [(C.LOOKUP_FILE, f"{C.BASE_URL}/misc/taxi_zone_lookup.csv", "TLC zone lookup"),
                         (C.CRZ_FILE, "https://data.ny.gov (MTA Central Business District Taxi Zones, dataset yfdc-w5jh per 03)",
                          "CRZ zone list, saved by the human 2026-11-13"),
                         (C.SHAPEFILE, f"{C.BASE_URL}/misc/taxi_zones.zip", "TLC zone shapefile (.shp; .dbf/.shx/.prj/.cpg beside it)")]:
        n = len(pd.read_csv(p)) if p.suffix == ".csv" else None
        entries.append({"name": p.name, "file_path": f"data/{p.name}", "source_url": url,
                        "license": "no explicit licence on TLC page; terms not found, checked 2026-11-13",
                        "downloaded_on": C.DOWNLOAD_DATE, "row_count": n,
                        "checksum": {"algorithm": "sha256", "value": L.sha256(p)}, "notes": note})
    L.write_manifest(entries)
    print("\nmanifest entries written:", len(entries))


if __name__ == "__main__":
    main()
