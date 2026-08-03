"""Tests for pipeline.clean.
pipeline.clean 테스트."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.clean import clean, drop_null_revenue, get_eligible_listings


@pytest.fixture()
def raw_listings() -> pd.DataFrame:
    """Small synthetic listings DataFrame covering every license/revenue edge case.
    license/revenue의 모든 경계 케이스를 포함한 작은 합성 listings DataFrame.
    """
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "license": [None, "Exempt", "STR-0001", None],
            "estimated_revenue_l365d": [1000.0, 0.0, np.nan, 500.0],
            "minimum_nights": [2, 45, 10, 30],
        }
    )


def test_clean_license_status_flag(raw_listings):
    result = clean(raw_listings)
    # NULL license -> Unlicensed, 'Exempt' -> Exempt, anything else -> Licensed.
    assert result["license_status"].tolist() == [
        "Unlicensed",
        "Exempt",
        "Licensed",
        "Unlicensed",
    ]


def test_clean_is_active_flag(raw_listings):
    result = clean(raw_listings)
    # revenue > 0 -> True, revenue == 0 -> False (not missing!), NaN revenue -> NA.
    assert result.loc[0, "is_active"] is True
    assert result.loc[1, "is_active"] is False
    assert pd.isna(result.loc[2, "is_active"])
    assert result.loc[3, "is_active"] is True


def test_clean_does_not_mutate_input(raw_listings):
    original = raw_listings.copy(deep=True)
    clean(raw_listings)
    pd.testing.assert_frame_equal(raw_listings, original)


def test_clean_output_row_count_unchanged(raw_listings):
    result = clean(raw_listings)
    assert len(result) == len(raw_listings)


def test_get_eligible_listings_filters_minimum_nights(raw_listings):
    result = get_eligible_listings(raw_listings)
    # Only rows with minimum_nights < 30 (rows 0 and 2) should remain.
    assert sorted(result["id"].tolist()) == [1, 3]


def test_drop_null_revenue(raw_listings):
    result = drop_null_revenue(raw_listings)
    assert result["estimated_revenue_l365d"].isna().sum() == 0
    assert len(result) == len(raw_listings) - 1
