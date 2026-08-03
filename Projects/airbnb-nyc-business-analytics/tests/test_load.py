"""Tests for pipeline.load.
pipeline.load 테스트.

Uses a small synthetic SQLite database (built in a pytest tmp_path fixture)
instead of the real ~30k-row airbnb_nyc.sqlite, so tests stay fast and don't
depend on the data file being present.
실제 ~3만 행짜리 airbnb_nyc.sqlite 대신, pytest tmp_path fixture로 만든
작은 합성 SQLite DB를 사용한다 — 테스트가 빠르고 데이터 파일 존재 여부에
의존하지 않는다.
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from pipeline.load import get_connection, load_raw


@pytest.fixture()
def sample_db(tmp_path):
    """Create a tiny SQLite DB with the same 3 tables as airbnb_nyc.sqlite.
    airbnb_nyc.sqlite와 동일한 3개 테이블을 가진 작은 SQLite DB를 생성한다.
    """
    db_path = tmp_path / "sample.sqlite"
    with sqlite3.connect(db_path) as conn:
        pd.DataFrame(
            {
                "id": [1, 2, 3],
                "neighbourhood_group_cleansed": ["Manhattan", "Brooklyn", "Queens"],
                "room_type": ["Entire home/apt", "Private room", "Entire home/apt"],
                "estimated_revenue_l365d": [1000.0, 0.0, None],
                "minimum_nights": [2, 45, 10],
                "license": [None, "Exempt", "STR-0001"],
                "host_id": [10, 20, 10],
            }
        ).to_sql("listings", conn, index=False)
        pd.DataFrame(
            {
                "listing_id": [1, 1, 2],
                "date": ["2026-01-01", "2026-01-02", "2026-01-01"],
                "available": ["t", "f", "t"],
            }
        ).to_sql("calendar", conn, index=False)
        pd.DataFrame(
            {
                "listing_id": [1, 2],
                "id": [100, 101],
                "date": ["2024-05-01", "2024-06-01"],
            }
        ).to_sql("reviews", conn, index=False)
    return db_path


def test_load_raw_listings(sample_db):
    df = load_raw(sample_db, "listings")
    assert len(df) == 3
    assert "estimated_revenue_l365d" in df.columns


def test_load_raw_calendar(sample_db):
    df = load_raw(sample_db, "calendar")
    assert len(df) == 3
    assert set(df.columns) == {"listing_id", "date", "available"}


def test_load_raw_reviews(sample_db):
    df = load_raw(sample_db, "reviews")
    assert len(df) == 2
    assert "date" in df.columns


def test_load_raw_invalid_table(sample_db):
    with pytest.raises(ValueError, match="Unknown table"):
        load_raw(sample_db, "not_a_real_table")


def test_load_raw_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.sqlite"
    with pytest.raises(FileNotFoundError):
        load_raw(missing_path, "listings")


def test_get_connection_runs_query(sample_db):
    with get_connection(sample_db) as conn:
        result = pd.read_sql("SELECT COUNT(*) AS n FROM listings", conn)
    assert result.loc[0, "n"] == 3


def test_get_connection_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.sqlite"
    with pytest.raises(FileNotFoundError):
        get_connection(missing_path)
