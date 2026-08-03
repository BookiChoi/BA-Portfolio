"""Tests for the pandas-only (non-SQL) functions in pipeline.analyze.
pipeline.analyze 중 SQL을 사용하지 않는 순수 pandas 함수 테스트.

The SQL-backed `analyze_*` functions (market segmentation, review trend,
license risk, host ranking) are exercised end-to-end by `main.py` against the
real database and are intentionally not re-tested here with a mocked
connection — the SQL itself is the thing worth validating, and mocking it
away would test very little.
SQL 기반 `analyze_*` 함수(시장 세분화, 리뷰 추이, 라이선스 리스크, 호스트 랭킹)는
실제 DB를 대상으로 `main.py`에서 end-to-end로 검증되며, mock connection으로
여기서 재검증하지 않는다 — 검증할 가치가 있는 것은 SQL 자체이며, mock으로
대체하면 테스트 의미가 거의 없어진다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.analyze import (
    analyze_growth_rates,
    check_license_borough_independence,
    find_growth_crossover,
    gini_coefficient,
    hosts_needed_for_target,
    summarize_revenue_at_risk,
)


# ---------------------------------------------------------------------------
# gini_coefficient
# ---------------------------------------------------------------------------


def test_gini_coefficient_perfect_equality():
    values = [100, 100, 100, 100]
    assert gini_coefficient(values) == pytest.approx(0.0, abs=1e-9)


def test_gini_coefficient_maximal_inequality():
    # One host holds (almost) everything -> Gini approaches 1 as n grows.
    values = [0, 0, 0, 1000]
    assert gini_coefficient(values) > 0.7


def test_gini_coefficient_bounded_between_0_and_1():
    values = np.random.default_rng(42).exponential(scale=1000, size=50)
    g = gini_coefficient(values)
    assert 0.0 <= g <= 1.0


# ---------------------------------------------------------------------------
# hosts_needed_for_target
# ---------------------------------------------------------------------------


def test_hosts_needed_for_target():
    host_rank = pd.DataFrame({"cumulative_pct": [40.0, 65.0, 82.0, 95.0, 100.0]})
    assert hosts_needed_for_target(host_rank, 50) == 2
    assert hosts_needed_for_target(host_rank, 80) == 3
    assert hosts_needed_for_target(host_rank, 100) == 5


# ---------------------------------------------------------------------------
# analyze_growth_rates
# ---------------------------------------------------------------------------


def test_analyze_growth_rates_detects_positive_trend():
    years = list(range(2010, 2020))
    # Perfect 10%/year compounding growth, no noise.
    manhattan = [100 * (1.10**i) for i in range(len(years))]
    trend_pivot = pd.DataFrame({"Manhattan": manhattan}, index=years)

    result = analyze_growth_rates(
        trend_pivot,
        boroughs=("Manhattan",),
        pre_covid_years=(2010, 2019),
        post_covid_years=(2010, 2019),  # same range twice is fine for this test
    )
    pre = result[result["period"].str.startswith("Pre-COVID")].iloc[0]
    assert pre["annual_growth_pct"] == pytest.approx(10.0, abs=0.5)
    assert pre["significant"]


# ---------------------------------------------------------------------------
# find_growth_crossover
# ---------------------------------------------------------------------------


def test_find_growth_crossover_detects_switch():
    years = [2018, 2019, 2020, 2021, 2022]
    trend_pivot = pd.DataFrame(
        {
            "Manhattan": [50, 40, 20, 60, 90],
            "Brooklyn": [60, 70, 30, 55, 80],
        },
        index=years,
    )
    result = find_growth_crossover(trend_pivot, covid_year=2020)
    # Brooklyn leads (Manhattan - Brooklyn < 0) in 2018, 2019, 2020.
    assert result["b_leads_from"] == 2018
    assert result["b_leads_until"] == 2020
    # Manhattan reclaims the lead at/after 2020 -> first positive gap is 2021.
    assert result["a_reclaims_from"] == 2021
    assert result["latest_gap"] == pytest.approx(10.0)


def test_find_growth_crossover_no_lead_change_returns_none():
    years = [2020, 2021, 2022]
    trend_pivot = pd.DataFrame(
        {"Manhattan": [100, 110, 120], "Brooklyn": [10, 12, 14]}, index=years
    )
    result = find_growth_crossover(trend_pivot, covid_year=2020)
    assert result["b_leads_from"] is None
    assert result["b_leads_until"] is None


# ---------------------------------------------------------------------------
# summarize_revenue_at_risk
# ---------------------------------------------------------------------------


def test_summarize_revenue_at_risk():
    risk = pd.DataFrame(
        {
            "borough": ["Manhattan", "Manhattan", "Brooklyn", "Brooklyn"],
            "license_status": ["Unlicensed", "Licensed", "Unlicensed", "Licensed"],
            "listing_count": [80, 20, 20, 80],
            "total_revenue": [800_000, 200_000, 100_000, 400_000],
        }
    )
    overall, unlicensed_by_borough = summarize_revenue_at_risk(risk)

    assert overall.loc["Unlicensed", "listing_count"] == 100
    assert overall.loc["Unlicensed", "listing_share_pct"] == pytest.approx(50.0)

    # Manhattan holds 80 of the 100 total unlicensed listings -> 80% share.
    manhattan_row = unlicensed_by_borough[
        unlicensed_by_borough["borough"] == "Manhattan"
    ].iloc[0]
    assert manhattan_row["share_of_all_unlicensed_pct"] == pytest.approx(80.0)
    # Sorted by listing_count descending -> Manhattan (80) should be first.
    assert unlicensed_by_borough.iloc[0]["borough"] == "Manhattan"


# ---------------------------------------------------------------------------
# check_license_borough_independence
# ---------------------------------------------------------------------------


def test_check_license_borough_independence_detects_association():
    # Strong association: Manhattan is almost all Unlicensed, Brooklyn almost all Licensed.
    risk = pd.DataFrame(
        {
            "borough": ["Manhattan", "Manhattan", "Brooklyn", "Brooklyn"],
            "license_status": ["Unlicensed", "Licensed", "Unlicensed", "Licensed"],
            "listing_count": [95, 5, 5, 95],
        }
    )
    result = check_license_borough_independence(risk)
    assert result["significant"]
    assert result["p_value"] < 0.05


def test_check_license_borough_independence_no_association():
    # No association: same 50/50 split in both boroughs.
    risk = pd.DataFrame(
        {
            "borough": ["Manhattan", "Manhattan", "Brooklyn", "Brooklyn"],
            "license_status": ["Unlicensed", "Licensed", "Unlicensed", "Licensed"],
            "listing_count": [50, 50, 50, 50],
        }
    )
    result = check_license_borough_independence(risk)
    assert not result["significant"]
