"""Validator sensitivity: does removing exact key duplicates (pickup, dropoff, PU, DO) change Q4 yellow/HVFHV shares or the decision?
Also: how many key duplicates are full-row duplicates (one sample file per year)."""
import duckdb, pandas as pd
from pathlib import Path
ROOT = Path("/Users/booki/Desktop/BA-Portfolio/Projects/nyc-congestion-pricing")
lk = pd.read_csv(ROOT / "data/taxi_zone_lookup.csv")
valid = sorted(set(lk.LocationID) - {264, 265})
crz = sorted(pd.read_csv(ROOT / "data/MTA_Central_Business_District_Taxi_Zones_20261113.csv")["Taxi Zone"].astype(int).unique())
con = duckdb.connect(); con.execute("PRAGMA threads=8")
con.execute(f"create table valid(id int); insert into valid values {','.join(f'({i})' for i in valid)}")
con.execute(f"create table crz(id int); insert into crz values {','.join(f'({i})' for i in crz)}")
for svc in ("yellow", "fhvhv"):
    pc = "tpep_pickup_datetime" if svc == "yellow" else "pickup_datetime"
    dc = "tpep_dropoff_datetime" if svc == "yellow" else "dropoff_datetime"
    out = {}
    for y in (2023, 2024, 2026):
        num = den = num2 = den2 = 0
        for m in range(1, 10):
            f = ROOT / f"data/{svc}_tripdata_{y}-{m:02d}.parquet"
            q = f"""select count(*) n, count(*) filter (where pu in (select id from valid) and dof in (select id from valid)) den,
                    count(*) filter (where pu in (select id from valid) and dof in (select id from valid) and (pu in (select id from crz) or dof in (select id from crz))) num
                    from (select {{src}} ) x"""
            raw = f"select {pc} p, {dc} d, PULocationID pu, DOLocationID dof from read_parquet('{f}') where year({pc})={y} and month({pc})={m}"
            a = con.execute(q.replace("{src}", "* from (" + raw + ")")).fetchone()
            b = con.execute(q.replace("{src}", "* from (select distinct * from (" + raw + "))")).fetchone()
            num += a[2]; den += a[1]; num2 += b[2]; den2 += b[1]
        out[y] = (num / den, num2 / den2, den, den2)
        print(svc, y, "share raw %.5f dedup %.5f  denom raw %d dedup %d (removed %.3f%%)" % (num / den, num2 / den2, den, den2, 100 * (1 - den2 / den)), flush=True)
    dm, dd = out[2026][0] - out[2024][0], out[2024][0] - out[2023][0]
    dm2, dd2 = out[2026][1] - out[2024][1], out[2024][1] - out[2023][1]
    print(svc, "raw  main %.3f pp drift %.3f pp margin %.3f pp" % (dm * 100, dd * 100, (abs(dm) - abs(dd)) * 100))
    print(svc, "dedup main %.3f pp drift %.3f pp margin %.3f pp" % (dm2 * 100, dd2 * 100, (abs(dm2) - abs(dd2)) * 100), flush=True)
# full-row duplicates in sample yellow files
for ym in ("2023-06", "2024-06", "2026-06"):
    f = ROOT / f"data/yellow_tripdata_{ym}.parquet"
    n = con.execute(f"select count(*) from read_parquet('{f}')").fetchone()[0]
    k = con.execute(f"select count(*) from (select distinct tpep_pickup_datetime, tpep_dropoff_datetime, PULocationID, DOLocationID from read_parquet('{f}'))").fetchone()[0]
    fr = con.execute(f"select count(*) from (select distinct * from read_parquet('{f}'))").fetchone()[0]
    print("yellow", ym, "rows", n, "key-duplicate rows", n - k, "full-row duplicate rows", n - fr, flush=True)
