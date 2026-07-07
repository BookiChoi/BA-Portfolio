"""Tests for pipeline.clean."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.clean import clean

def test_clean_removes_duplicate_rows() -> None:
    """clean should remove fully duplicated rows."""
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "value": ["a", "a", "b"],
        }
    )

    result = clean(df)

    assert len(result) == 2

def test_clean_handles_fully_empty_rows() -> None:
    """clean should drop rows where every value is missing."""
    df = pd.DataFrame(
        {
            "id": [1, np.nan, 2],
            "value": ["a", np.nan, "b"],
        }
    )

    result = clean(df)

    assert not result.isna().all(axis=1).any()
    assert len(result) == 2

def test_clean_returns_dataframe() -> None:
    """clean should always return a DataFrame, even for simple input."""
    df = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    result = clean(df)

    assert isinstance(result, pd.DataFrame)
