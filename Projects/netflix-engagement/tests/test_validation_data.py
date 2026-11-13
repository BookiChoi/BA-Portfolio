"""Validator: independent raw-data checks (row counts vs manifest, duplicates, missing, half totals).

Own reader (openpyxl only), does not use pipeline.load or pipeline.profile_reports.
Run: pytest -q -s tests/test_validation_data.py
"""
import json
import os
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
NF = Path(os.path.expanduser("~/Downloads/netflix-reports"))
FILES = ["2023Jan-Jun.xlsx", "2023Jul-Dec.xlsx", "2024Jan-Jun.xlsx", "2024Jul-Dec.xlsx",
         "2025Jan-Jun.xlsx", "2025Jul-Dec.xlsx", "2026Jan-Jun.xlsx"]
HALVES = ["H1 2023", "H2 2023", "H1 2024", "H2 2024", "H1 2025", "H2 2025", "H1 2026"]


def read_file(fname):
    wb = openpyxl.load_workbook(NF / fname, read_only=True, data_only=True)
    frames = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        h = next(i for i, r in enumerate(rows[:40]) if any(isinstance(c, str) and c.strip().lower() == "title" for c in r))
        hdr = [str(c).strip() if c is not None else None for c in rows[h]]
        ti = next(i for i, c in enumerate(hdr) if c and c.lower() == "title")
        hi = next(i for i, c in enumerate(hdr) if c and "hours" in c.lower() and "view" in c.lower())
        recs = []
        for r in rows[h + 1:]:
            t = r[ti] if ti < len(r) else None
            hv = r[hi] if hi < len(r) else None
            rest = [c for j, c in enumerate(r) if j not in (ti,) and c is not None]
            if t is None or str(t).strip() == "":
                continue
            if not rest:  # footnote row: text in title only
                continue
            recs.append({"sheet": ws.title, "title": str(t).strip(), "hours": hv})
        df = pd.DataFrame(recs)
        df["file"] = fname
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


@pytest.fixture(scope="module")
def raw():
    return {f: read_file(f) for f in FILES}


def test_row_counts_and_quality(raw):
    man = {d["name"]: d["row_count"] for d in json.loads((ROOT / "data_manifest.json").read_text())["datasets"]}
    tot = 0
    for f in FILES:
        df = raw[f]
        n = len(df)
        hrs = pd.to_numeric(df["hours"], errors="coerce")
        miss = int(hrs.isna().sum())
        nonpos = int((hrs <= 0).sum())
        dup_full = int(df.duplicated(["sheet", "title", "hours"]).sum())
        dup_title_sheet = int(df.duplicated(["sheet", "title"]).sum())
        dup_title_all = int(df.duplicated(["title"]).sum())
        print(f"ROWS {f}: n={n} manifest={man[f]} missing_hours={miss} nonpos={nonpos} "
              f"dup_full={dup_full} dup_title_in_sheet={dup_title_sheet} dup_title_across_sheets={dup_title_all} "
              f"sum_hours={hrs.sum():.0f}")
        tot += n
        assert n == man[f]
        assert miss == 0 and nonpos == 0
    print("TOTAL ROWS", tot)
    assert tot == 115956


def test_half_totals_vs_coverage_csv(raw):
    cov = pd.read_csv(ROOT / "outputs" / "q1" / "coverage_by_half.csv")
    for f, h in zip(FILES, HALVES):
        mine = pd.to_numeric(raw[f]["hours"]).sum()
        theirs = float(cov.loc[cov.half == h, "all_listed_hours"].iloc[0])
        print(f"TOTAL {h}: mine={mine:.0f} analyst_all_listed={theirs:.0f} diff={mine - theirs:.0f}")
        assert abs(mine - theirs) < 1.0
