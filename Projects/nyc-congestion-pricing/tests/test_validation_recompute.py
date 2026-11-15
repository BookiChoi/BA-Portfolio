"""Validator tests (independent of the analyst code). Run inside the project folder: pytest -q tests/test_validation_recompute.py

1. Row counts of three parquet files equal data_manifest.json (pyarrow metadata, no row read).
2. Yellow 2024-01 Q4 monthly in-zone share, recomputed with DuckDB SQL, equals the analyst's q4_monthly_share.csv.
3. The saved validator check table (workflow/logs/validation_checks.csv, produced by validation_recompute.py) has no failed check.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_row_counts_match_parquet_metadata():
    pq = pytest.importorskip("pyarrow.parquet")
    man = {d["name"]: d["row_count"] for d in json.load(open(ROOT / "data_manifest.json"))["datasets"]}
    for name in ("yellow_tripdata_2024-01.parquet", "fhvhv_tripdata_2023-02.parquet", "yellow_tripdata_2026-09.parquet"):
        p = ROOT / "data" / name
        if not p.exists():
            pytest.skip("data not present")
        assert pq.ParquetFile(p).metadata.num_rows == man[name]


def test_q4_monthly_share_yellow_2024_01_duckdb():
    duckdb = pytest.importorskip("duckdb")
    f = ROOT / "data/yellow_tripdata_2024-01.parquet"
    if not f.exists():
        pytest.skip("data not present")
    lk = pd.read_csv(ROOT / "data/taxi_zone_lookup.csv")
    valid = sorted(set(lk.LocationID) - {264, 265})
    crz = sorted(pd.read_csv(ROOT / "data/MTA_Central_Business_District_Taxi_Zones_20261113.csv")["Taxi Zone"].astype(int))
    v, c = ",".join(map(str, valid)), ",".join(map(str, crz))
    num, den = duckdb.sql(f"""select count(*) filter (where PULocationID in ({c}) or DOLocationID in ({c})),
        count(*) from read_parquet('{f}') where year(tpep_pickup_datetime)=2024 and month(tpep_pickup_datetime)=1
        and PULocationID in ({v}) and DOLocationID in ({v})""").fetchone()
    a = pd.read_csv(ROOT / "outputs/q4/q4_monthly_share.csv")
    a = a[(a.service == "yellow") & (a.year == 2024) & (a.month == 1)].iloc[0]
    assert num / den == pytest.approx(a.share, abs=1e-12)
    assert den == a.valid_denominator


def test_saved_validation_checks_have_no_failures():
    p = ROOT / "workflow/logs/validation_checks.csv"
    if not p.exists():
        pytest.skip("validation_checks.csv not generated")
    d = pd.read_csv(p)
    assert len(d) > 500
    assert d["pass"].all(), d[~d["pass"]].number.tolist()
