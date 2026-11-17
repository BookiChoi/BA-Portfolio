"""Validator: independent per-file aggregation with DuckDB SQL (analyst used pyarrow). Output: pickles in workflow/logs/validation_cache."""
import pickle, time, pandas as pd, duckdb
from pathlib import Path
ROOT = Path("/Users/booki/Desktop/BA-Portfolio/Projects/nyc-congestion-pricing")
OUT = ROOT / "workflow/logs/validation_cache"; OUT.mkdir(parents=True, exist_ok=True)
lk = pd.read_csv(ROOT/"data/taxi_zone_lookup.csv")
bad = lk[lk["Borough"].isin(["Unknown", "N/A"]) | lk["Zone"].isin(["Unknown", "Outside of NYC", "N/A"])]
valid = sorted(set(lk.LocationID) - set(bad.LocationID))
crz = sorted(pd.read_csv(ROOT/"data/MTA_Central_Business_District_Taxi_Zones_20261113.csv")["Taxi Zone"].astype(int).unique())
print("lookup rows", len(lk), "invalid ids", sorted(bad.LocationID), "n valid", len(valid), "n crz", len(crz), flush=True)
months = sorted({(y, m) for y in (2023, 2024, 2026) for m in range(1, 10)} | {(2025, 10), (2025, 11), (2025, 12)})
con = duckdb.connect(); con.execute("PRAGMA threads=8")
con.execute(f"create table valid(id int); insert into valid values {','.join(f'({i})' for i in valid)}")
con.execute(f"create table crz(id int); insert into crz values {','.join(f'({i})' for i in crz)}")
res = {}
for svc in ("yellow", "fhvhv"):
    pc = "tpep_pickup_datetime" if svc == "yellow" else "pickup_datetime"
    dc = "tpep_dropoff_datetime" if svc == "yellow" else "dropoff_datetime"
    for (y, m) in months:
        t0 = time.time()
        f = ROOT/f"data/{svc}_tripdata_{y}-{m:02d}.parquet"
        has_fee = "cbd_congestion_fee" in [r[0] for r in con.execute(f"describe select * from read_parquet('{f}')").fetchall()]
        con.execute(f"""create or replace temp table t as select {pc} p, cast(PULocationID as bigint) pu, cast(DOLocationID as bigint) dof,
            {('cbd_congestion_fee' if has_fee else 'cast(null as double)')} fee, {dc} d from read_parquet('{f}')""")
        r = {}
        r["total"], r["null_pickup"] = con.execute("select count(*), count(*) filter (where p is null) from t").fetchone()
        r["dup_key"] = con.execute("select count(*) - (select count(*) from (select distinct p,d,pu,dof from t)) from t").fetchone()[0]
        con.execute(f"create or replace temp table u as select * from t where year(p)={y} and month(p)={m}")
        r["in_month"] = con.execute("select count(*) from u").fetchone()[0]
        r["null_pu"], r["null_do"] = con.execute("select count(*) filter (where pu is null), count(*) filter (where dof is null) from u").fetchone()
        r["inv_pu"] = con.execute("select count(*) from u where pu is null or pu not in (select id from valid)").fetchone()[0]
        r["inv_do"] = con.execute("select count(*) from u where dof is null or dof not in (select id from valid)").fetchone()[0]
        r["dhp"] = con.execute("select cast(p as date) date, hour(p) hr, coalesce(pu,-1) pu, count(*) n from u group by all").df()
        r["flags"] = con.execute("""select cast(p as date) date, (pu in (select id from valid)) vpu, (dof in (select id from valid)) vdo,
            (pu in (select id from crz) or dof in (select id from crz)) inz, count(*) n from u group by all""").df()
        r["airport"] = con.execute("select cast(p as date) date, pu, coalesce(dof,-1) dof, count(*) n from u where pu in (1,132,138) group by all").df()
        r["do"] = con.execute("select coalesce(dof,-1) dof, count(*) n from u group by all").df()
        if has_fee:
            r["fee"] = con.execute("""select cast(p as date) date, coalesce(pu,-1) pu, (dof in (select id from valid)) vdo,
              (pu in (select id from crz) or dof in (select id from crz)) inz, case when fee is null then 0 when fee>0 then 2 else 1 end fs, count(*) n
              from u group by all""").df()
        res[(svc, y, m)] = r
        print(svc, y, m, r["total"], r["in_month"], f"{time.time()-t0:.1f}s", flush=True)
pickle.dump(res, open(OUT/"agg.pkl", "wb"))
pickle.dump({"valid": valid, "crz": crz}, open(OUT/"ids.pkl", "wb"))
print("done")
