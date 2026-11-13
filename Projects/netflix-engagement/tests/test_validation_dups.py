"""Validator: duplicates judged on every column (analyst clean_log reports duplicate_full_rows = 0)."""
import os
from pathlib import Path

import openpyxl
import pandas as pd

NF = Path(os.path.expanduser("~/Downloads/netflix-reports"))
FILES = ["2023Jan-Jun.xlsx", "2023Jul-Dec.xlsx", "2024Jan-Jun.xlsx", "2024Jul-Dec.xlsx",
         "2025Jan-Jun.xlsx", "2025Jul-Dec.xlsx", "2026Jan-Jun.xlsx"]


def test_full_row_duplicates_all_columns():
    n_dup = n_rows = 0
    for f in FILES:
        wb = openpyxl.load_workbook(NF / f, read_only=True, data_only=True)
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            h = next(i for i, r in enumerate(rows[:40]) if any(isinstance(c, str) and c.strip().lower() == "title" for c in r))
            cols = [str(c) if c is not None else f"_c{i}" for i, c in enumerate(rows[h])]
            df = pd.DataFrame(rows[h + 1:], columns=cols)
            tcol = next(c for c in cols if c.strip().lower() == "title")
            df = df[df[tcol].notna()]
            n_rows += len(df)
            dd = df[df.duplicated(keep=False)]
            n_dup += int(df.duplicated().sum())
            if len(dd):
                print("FULLDUP", f, ws.title, dd.to_dict("records"))
            tt = df[df.duplicated(tcol, keep=False)]
            if len(tt):
                print("TITLEDUP", f, ws.title, tt.to_dict("records"))
    print("ROWS CHECKED", n_rows, "FULL-ROW DUPLICATES (all columns):", n_dup)
    assert n_dup == 0
