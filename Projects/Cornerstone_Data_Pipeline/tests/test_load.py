"""Tests for pipeline.load."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.load import load_raw

def test_load_raw_returns_dataframe(tmp_path: Path) -> None:
    """load_raw should return a pandas DataFrame."""
    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("col_a,col_b\n1,x\n2,y\n")

    result = load_raw(str(csv_path))

    assert isinstance(result, pd.DataFrame)

def test_load_raw_loads_csv_contents_correctly(tmp_path: Path) -> None:
    """load_raw should load the CSV contents without altering them."""
    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("col_a,col_b\n1,x\n2,y\n")

    result = load_raw(str(csv_path))

    expected = pd.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})
    pd.testing.assert_frame_equal(result, expected)
