"""Aggregate all 60 files to count tables in outputs/cache (resumable: existing files are reused)."""
import json
import os
import time

import pandas as pd

from . import aggregate as A, config as C, load as L


def main():
    lk = L.read_lookup()
    invalid = set(L.invalid_zone_ids(lk))
    valid_ids = set(lk.LocationID) - invalid
    crz_ids = set(pd.read_csv(C.OUT / "reference" / "crz_zone_ids.csv").LocationID)
    print("valid zone IDs:", len(valid_ids), "invalid:", sorted(invalid), "CRZ IDs:", len(crz_ids))
    C.CACHE.mkdir(parents=True, exist_ok=True)
    qrows = []
    for s in C.SERVICES:
        for ym in C.ALL_MONTHS:
            tag = f"{s}_{ym[0]}-{ym[1]:02d}"
            cj = C.CACHE / f"{tag}_counts.json"
            if cj.exists() and not os.environ.get("FORCE_AGG"):   # FORCE_AGG=1 rebuilds every file
                counts = json.loads(cj.read_text())
            else:
                t0 = time.time()
                tabs, counts = A.aggregate_file(s, ym, valid_ids, crz_ids)
                for k, df in tabs.items():
                    df.to_parquet(C.CACHE / f"{tag}_{k}.parquet", index=False)
                cj.write_text(json.dumps(counts))
                print(f"{tag}: {time.time() - t0:.1f}s", counts, flush=True)
            qrows.append({"service": s, "year": ym[0], "month": ym[1], **counts})
    q = pd.DataFrame(qrows)
    q.to_csv(C.OUT / "reference" / "file_quality_counts.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 100)
    print(q.to_string(index=False))
    print("\ntotals per service:")
    print(q.groupby("service")[["rows_total", "null_pickup", "out_of_month", "rows_in_month", "invalid_pu", "invalid_do"]].sum())


if __name__ == "__main__":
    main()
