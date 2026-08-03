"""Cross-validate pipeline.clean's pandas rules against pipeline.analyze's SQL.
pipeline.clean의 pandas 규칙과 pipeline.analyze의 SQL을 상호 검증한다.

WHY this file exists / 이 파일이 존재하는 이유:
`clean.py` derives `license_status` / `is_active` / eligibility with pandas,
while `analyze.py` derives the exact same business rules independently with
raw SQL (`CASE WHEN`, `WHERE minimum_nights < ...`) so that Q1-Q4 can
showcase JOIN / GROUP BY / CTE / window functions directly against SQLite.
That means the same rule is implemented twice, in two languages — a real
risk if one is changed without the other.

Rather than collapsing the duplication (which would remove the SQL from the
SQL-technique demo), this test proves both implementations agree on the real
database. If they ever drift, this test — not a demo audience — is the one
that catches it.

`clean.py`는 pandas로, `analyze.py`는 순수 SQL(`CASE WHEN`,
`WHERE minimum_nights < ...`)로 `license_status` / `is_active` / 등록 대상
여부를 각각 독립적으로 파생한다. Q1~Q4가 SQLite에 대한 JOIN / GROUP BY / CTE /
윈도우 함수를 직접 보여주기 위한 의도적 구조이지만, 그만큼 같은 규칙이 두
언어로 두 번 구현되는 위험이 있다.

중복 자체를 없애는 대신(그러면 SQL 기법을 보여줄 곳이 사라짐), 이 테스트는
두 구현이 실제 DB에서 동일한 결론에 도달하는지 증명한다. 나중에 둘이
어긋나면, 발표 자리가 아니라 이 테스트가 먼저 잡아낸다.

Skipped automatically if the real database is not present (e.g. in CI without
the data file).
실제 DB 파일이 없으면(예: 데이터 파일이 없는 CI 환경) 자동으로 스킵된다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from pipeline.clean import _add_is_active_flag, _add_license_status, get_eligible_listings
from pipeline.constants import REGISTRATION_MIN_NIGHTS_THRESHOLD

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "airbnb_nyc.sqlite"

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason=f"Real database not found at {DB_PATH} — skipping cross-validation.",
)


@pytest.fixture(scope="module")
def raw_listings() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM listings", conn)


def test_license_status_matches_sql_case_when(raw_listings):
    """pandas `_add_license_status` must classify every row exactly like the
    SQL `CASE WHEN license IS NULL THEN 'Unlicensed' WHEN license = 'Exempt'
    THEN 'Exempt' ELSE 'Licensed' END` used in `analyze.py` (unfiltered —
    same population, no eligibility filter applied on either side).
    pandas `_add_license_status`는 `analyze.py`가 쓰는 SQL
    `CASE WHEN license IS NULL THEN 'Unlicensed' WHEN license = 'Exempt'
    THEN 'Exempt' ELSE 'Licensed' END`과 (등록 대상 필터 없이, 동일한
    전체 population에 대해) 정확히 같은 결과를 내야 한다.
    """
    pandas_counts = _add_license_status(raw_listings)["license_status"].value_counts().to_dict()

    with sqlite3.connect(DB_PATH) as conn:
        sql_counts = pd.read_sql(
            """
            SELECT
                CASE
                    WHEN license IS NULL   THEN 'Unlicensed'
                    WHEN license = 'Exempt' THEN 'Exempt'
                    ELSE 'Licensed'
                END AS license_status,
                COUNT(*) AS n
            FROM listings
            GROUP BY license_status
            """,
            conn,
        ).set_index("license_status")["n"].to_dict()

    assert pandas_counts == sql_counts


def test_eligible_listings_count_matches_sql_filter(raw_listings):
    """`get_eligible_listings()` (pandas `minimum_nights < 30`) must return the
    same row count as the SQL `WHERE minimum_nights < 30` filter used inside
    the `eligible_listings` CTE in `analyze.py` (Q3/Q4).
    `get_eligible_listings()`(pandas `minimum_nights < 30`)는 `analyze.py`
    (Q3/Q4)의 `eligible_listings` CTE 안 SQL `WHERE minimum_nights < 30`
    필터와 동일한 행 수를 반환해야 한다.
    """
    pandas_count = len(get_eligible_listings(raw_listings))

    with sqlite3.connect(DB_PATH) as conn:
        sql_count = pd.read_sql(
            f"SELECT COUNT(*) AS n FROM listings "
            f"WHERE minimum_nights < {REGISTRATION_MIN_NIGHTS_THRESHOLD}",
            conn,
        ).loc[0, "n"]

    assert pandas_count == int(sql_count)


def test_license_status_matches_sql_on_eligible_subset(raw_listings):
    """The same license_status agreement must hold on the Q3/Q4 population —
    eligible listings only (`minimum_nights < 30`) — since that is the subset
    `analyze_license_risk_distribution()` actually reports on.
    Q3/Q4가 실제로 다루는 population(`minimum_nights < 30`인 등록 대상
    매물만)에서도 동일한 license_status 결과가 나와야 한다 —
    `analyze_license_risk_distribution()`이 보고하는 대상이 바로 이 서브셋이다.
    """
    eligible = get_eligible_listings(raw_listings)
    pandas_counts = _add_license_status(eligible)["license_status"].value_counts().to_dict()

    with sqlite3.connect(DB_PATH) as conn:
        sql_counts = pd.read_sql(
            f"""
            WITH eligible_listings AS (
                SELECT * FROM listings WHERE minimum_nights < {REGISTRATION_MIN_NIGHTS_THRESHOLD}
            )
            SELECT
                CASE
                    WHEN license IS NULL   THEN 'Unlicensed'
                    WHEN license = 'Exempt' THEN 'Exempt'
                    ELSE 'Licensed'
                END AS license_status,
                COUNT(*) AS n
            FROM eligible_listings
            GROUP BY license_status
            """,
            conn,
        ).set_index("license_status")["n"].to_dict()

    assert pandas_counts == sql_counts


def test_is_active_matches_sql_active_rate(raw_listings):
    """pandas `is_active` (True/False/NA) must partition `estimated_revenue_l365d`
    exactly like the SQL `CASE WHEN estimated_revenue_l365d > 0 THEN 1.0 ELSE
    0.0 END` (`active_rate`) used in `analyze_market_segmentation()` — i.e. the
    same active / inactive / null-revenue counts, market-wide.
    pandas `is_active`(True/False/NA)는 `analyze_market_segmentation()`이
    쓰는 SQL `CASE WHEN estimated_revenue_l365d > 0 THEN 1.0 ELSE 0.0 END`
    (`active_rate`)과 동일하게 매출을 분할해야 한다 — 즉 시장 전체 기준으로
    활성/비활성/매출결측 건수가 같아야 한다.
    """
    flagged = _add_is_active_flag(raw_listings)["is_active"]
    pandas_active = int((flagged == True).sum())  # noqa: E712 — explicit tri-state check
    pandas_inactive = int((flagged == False).sum())  # noqa: E712
    pandas_null = int(flagged.isna().sum())

    with sqlite3.connect(DB_PATH) as conn:
        sql_row = pd.read_sql(
            """
            SELECT
                SUM(CASE WHEN estimated_revenue_l365d > 0 THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN estimated_revenue_l365d = 0 THEN 1 ELSE 0 END) AS inactive,
                SUM(CASE WHEN estimated_revenue_l365d IS NULL THEN 1 ELSE 0 END) AS null_revenue
            FROM listings
            """,
            conn,
        ).iloc[0]

    assert pandas_active == int(sql_row["active"])
    assert pandas_inactive == int(sql_row["inactive"])
    assert pandas_null == int(sql_row["null_revenue"])
