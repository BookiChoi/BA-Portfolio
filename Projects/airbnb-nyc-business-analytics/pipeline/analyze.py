"""Analytical functions — one function per business question.
분석 함수 — 비즈니스 질문당 함수 하나.

Rules:
- SQL-backed functions accept a `sqlite3.Connection` and return a DataFrame.
- Pandas-backed functions accept the output of another `analyze_*` function.
- No printing, no plotting, no side effects.
- Every function is independently unit-testable.
규칙:
- SQL 기반 함수는 `sqlite3.Connection`을 받아 DataFrame을 반환한다.
- pandas 기반 함수는 다른 `analyze_*` 함수의 출력을 받는다.
- 출력(print), 시각화(plot), 부작용(side effect) 없음.
- 모든 함수를 독립적으로 단위 테스트할 수 있다.

Business Questions / 비즈니스 질문 (see notebooks/airbnb_business_eda.ipynb)
------------------
Q1  Market Segmentation      — where is NYC short-term rental revenue concentrated?
                                단기 임대 매출은 어디에 집중되어 있는가?
Q2  Growth Trend              — is that growth real, and who is leading it now?
                                그 성장은 실재하며, 지금은 누가 주도하는가?
Q3  Risk Distribution         — how much of that revenue sits with unregistered hosts?
                                그 매출 중 얼마가 미등록 호스트에게 있는가?
Q4  Priority Ranking          — which hosts should compliance outreach target first?
                                컴플라이언스 담당자는 어떤 호스트부터 접촉해야 하는가?
"""

from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd
from scipy import stats

from pipeline.constants import (
    COVID_YEAR,
    POST_COVID_YEARS,
    PRE_COVID_YEARS,
    REGISTRATION_MIN_NIGHTS_THRESHOLD,
    TOP_4_SEGMENTS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Q1 — Market Segmentation / 시장 세분화
# ---------------------------------------------------------------------------


def analyze_market_segmentation(conn: sqlite3.Connection) -> pd.DataFrame:
    """Aggregate revenue and occupancy by borough x room type.
    자치구 x 룸타입별 매출과 점유율을 집계한다.

    [Aggregation and Mapping] JOIN(listings + calendar aggregate subquery)
    + GROUP BY(borough, room_type) + SUM/AVG/COUNT.

    So-what: Shows exactly where NYC short-term rental revenue is
    concentrated — the market map every other question builds on.
    so-what: NYC 단기 임대 매출이 정확히 어디에 집중되어 있는지 보여준다 —
    이후 모든 질문의 기반이 되는 시장 지도.

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.

    Returns:
        DataFrame with one row per (borough, room_type), sorted by
        `total_revenue` descending, including `revenue_share_pct` and
        `cumulative_share_pct` of total market revenue.
        (borough, room_type)별 1행, `total_revenue` 내림차순 정렬,
        전체 시장 매출 대비 `revenue_share_pct`·`cumulative_share_pct` 포함.
    """
    query = """
    SELECT
        l.neighbourhood_group_cleansed                              AS borough,
        l.room_type                                                 AS room_type,
        COUNT(*)                                                    AS listing_count,
        SUM(l.estimated_revenue_l365d)                              AS total_revenue,
        AVG(l.estimated_revenue_l365d)                              AS avg_revenue,
        AVG(CASE WHEN l.estimated_revenue_l365d > 0
                 THEN l.estimated_revenue_l365d END)                AS avg_revenue_active,
        AVG(CASE WHEN l.estimated_revenue_l365d > 0
                 THEN 1.0 ELSE 0.0 END)                              AS active_rate,
        AVG(cal.unavailable_days * 1.0 / cal.total_days)            AS avg_calendar_occupancy
    FROM listings AS l
    JOIN (
        SELECT listing_id,
               COUNT(*) AS total_days,
               SUM(CASE WHEN available = 'f' THEN 1 ELSE 0 END) AS unavailable_days
        FROM calendar
        GROUP BY listing_id
    ) AS cal
        ON l.id = cal.listing_id
    WHERE l.estimated_revenue_l365d IS NOT NULL
    GROUP BY borough, room_type
    ORDER BY total_revenue DESC
    """
    segment = pd.read_sql(query, conn)

    total_market_revenue = segment["total_revenue"].sum()
    segment["revenue_share_pct"] = (
        segment["total_revenue"] / total_market_revenue * 100
    ).round(2)
    segment["active_rate_pct"] = (segment["active_rate"] * 100).round(1)
    segment["cumulative_share_pct"] = segment["revenue_share_pct"].cumsum().round(2)

    logger.info(
        "Q1: %d segments computed, total market revenue $%.0f",
        len(segment),
        total_market_revenue,
    )
    return segment


def analyze_superhost_effect(
    conn: sqlite3.Connection, top_segments: tuple[tuple[str, str], ...] = TOP_4_SEGMENTS
) -> pd.DataFrame:
    """Compare superhost vs regular-host revenue within the top revenue segments.
    상위 매출 세그먼트 내 슈퍼호스트 vs 일반 호스트 매출을 비교한다.

    Runs a Mann-Whitney U test per segment (revenue is right-skewed, so a
    non-parametric test is used instead of a t-test).
    세그먼트별로 Mann-Whitney U 검정을 실행한다 (매출이 우편향이라 t-검정 대신
    비모수 검정을 사용).

    So-what: Validates the superhost program's ROI specifically where the
    market's money already is, not just on average across the whole market.
    so-what: 슈퍼호스트 프로그램의 ROI를 시장 전체 평균이 아니라, 매출이 실제로
    몰려 있는 곳에서 구체적으로 검증한다.

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.
        top_segments: (borough, room_type) pairs to compare. Defaults to the
                      top-4 revenue segments from `analyze_market_segmentation`.
                      비교할 (borough, room_type) 목록. 기본값은
                      `analyze_market_segmentation`의 매출 상위 4개 세그먼트.

    Returns:
        DataFrame with one row per segment: superhost/regular means, lift
        multiplier, and Mann-Whitney p-value, sorted by lift descending.
        세그먼트별 1행: 슈퍼호스트/일반 호스트 평균, 배율(lift), Mann-Whitney
        p-value. lift 내림차순 정렬.
    """
    conditions = " OR ".join(
        f"(neighbourhood_group_cleansed = '{borough}' AND room_type = '{room_type}')"
        for borough, room_type in top_segments
    )
    query = f"""
    SELECT neighbourhood_group_cleansed AS borough, room_type, host_is_superhost,
           estimated_revenue_l365d AS revenue
    FROM listings
    WHERE estimated_revenue_l365d IS NOT NULL
      AND host_is_superhost IN ('t', 'f')
      AND ({conditions})
    """  # noqa: S608 — conditions built from a fixed, non-user-supplied tuple
    sup_df = pd.read_sql(query, conn)

    results = []
    for (borough, room_type), g in sup_df.groupby(["borough", "room_type"]):
        sup = g[g["host_is_superhost"] == "t"]["revenue"]
        reg = g[g["host_is_superhost"] == "f"]["revenue"]
        u_stat, p_value = stats.mannwhitneyu(sup, reg, alternative="two-sided")
        results.append(
            {
                "borough": borough,
                "room_type": room_type,
                "superhost_n": len(sup),
                "superhost_mean": sup.mean(),
                "regular_n": len(reg),
                "regular_mean": reg.mean(),
                "lift_x": sup.mean() / reg.mean(),
                "u_statistic": u_stat,
                "p_value": p_value,
            }
        )
    result = pd.DataFrame(results).sort_values("lift_x", ascending=False).reset_index(
        drop=True
    )
    logger.info("Q1: superhost effect computed for %d segments", len(result))
    return result


def check_borough_revenue_difference(conn: sqlite3.Connection) -> dict:
    """Kruskal-Wallis H-test: does revenue differ significantly across boroughs?
    Kruskal-Wallis H-검정: 자치구 간 매출 차이가 통계적으로 유의한가?

    Restricted to `Entire home/apt` listings so the comparison isn't
    confounded by room-type mix differences between boroughs.
    자치구 간 룸타입 구성 차이에 검정 결과가 왜곡되지 않도록 `Entire home/apt`
    매물로 한정한다.

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.

    Returns:
        Dict with keys `h_statistic`, `p_value`, `significant` (p < 0.05).
        `h_statistic`, `p_value`, `significant`(p < 0.05) 키를 가진 dict.
    """
    query = """
    SELECT neighbourhood_group_cleansed AS borough, estimated_revenue_l365d AS revenue
    FROM listings
    WHERE room_type = 'Entire home/apt' AND estimated_revenue_l365d IS NOT NULL
    """
    raw = pd.read_sql(query, conn)
    groups = [g["revenue"].values for _, g in raw.groupby("borough")]
    h_stat, p_value = stats.kruskal(*groups)
    logger.info("Q1: Kruskal-Wallis H=%.2f, p=%.2e", h_stat, p_value)
    return {
        "h_statistic": float(h_stat),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05),
    }


# ---------------------------------------------------------------------------
# Q2 — Growth Trend / 성장 추이
# ---------------------------------------------------------------------------


def analyze_borough_review_trend(conn: sqlite3.Connection) -> pd.DataFrame:
    """Pivot yearly review counts by borough (a demand proxy over time).
    자치구별 연도별 리뷰 수를 피벗한다 (시간에 따른 수요 프록시).

    [Time-Based Trend] JOIN(reviews + listings) + strftime('%Y', date) date
    function + GROUP BY(borough, year).

    So-what: Tracks whether the market segments identified in Q1 are still
    growing, and which borough is driving that growth today.
    so-what: Q1에서 확인한 세그먼트가 여전히 성장 중인지, 지금은 어느
    자치구가 그 성장을 주도하는지 추적한다.

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.

    Returns:
        DataFrame indexed by `review_year` (int), one column per borough,
        values = review count. Missing combinations filled with 0.
        `review_year`(int) 인덱스, 자치구별 컬럼, 값은 리뷰 수.
        결측 조합은 0으로 채움.
    """
    query = """
    SELECT
        strftime('%Y', r.date)              AS review_year,
        l.neighbourhood_group_cleansed      AS borough,
        COUNT(*)                            AS review_count
    FROM reviews AS r
    JOIN listings AS l
        ON r.listing_id = l.id
    GROUP BY review_year, borough
    ORDER BY review_year, borough
    """
    trend = pd.read_sql(query, conn)
    trend["review_year"] = trend["review_year"].astype(int)
    trend_pivot = trend.pivot(
        index="review_year", columns="borough", values="review_count"
    ).fillna(0)
    logger.info(
        "Q2: review trend pivoted — %d years x %d boroughs",
        *trend_pivot.shape,
    )
    return trend_pivot


def analyze_growth_rates(
    trend_pivot: pd.DataFrame,
    boroughs: tuple[str, ...] = ("Manhattan", "Brooklyn"),
    pre_covid_years: tuple[int, int] = PRE_COVID_YEARS,
    post_covid_years: tuple[int, int] = POST_COVID_YEARS,
) -> pd.DataFrame:
    """Estimate annual growth rate pre- and post-COVID via log-linear regression.
    로그-선형 회귀로 코로나 이전/이후 연평균 성장률을 추정한다.

    WHY log-linear: a constant % growth rate is linear in log-space, so
    fitting `log(review_count) ~ year` and exponentiating the slope gives a
    single interpretable "%/year" figure, plus a p-value for significance.
    로그-선형인 이유: 일정한 % 성장률은 로그 공간에서 선형이므로,
    `log(리뷰수) ~ 연도`를 적합하고 기울기를 지수변환하면 해석 가능한
    "연간 %" 수치와 유의성 p-value를 함께 얻을 수 있다.

    Args:
        trend_pivot: Output of `analyze_borough_review_trend()`.
        boroughs: Boroughs to compute growth for.
        pre_covid_years: (start, end) inclusive year range before COVID.
        post_covid_years: (start, end) inclusive year range after COVID.

    Returns:
        DataFrame with columns [period, borough, annual_growth_pct,
        r_squared, p_value, significant].
        [period, borough, annual_growth_pct, r_squared, p_value, significant]
        컬럼의 DataFrame.
    """

    def _growth(sub: pd.Series) -> tuple[float, float, float]:
        slope, _intercept, r_value, p_value, _std_err = stats.linregress(
            sub.index, np.log(sub)
        )
        growth_pct = (np.exp(slope) - 1) * 100
        return growth_pct, r_value**2, p_value

    rows = []
    periods = [
        (f"Pre-COVID ({pre_covid_years[0]}-{pre_covid_years[1]})", pre_covid_years),
        (f"Post-COVID ({post_covid_years[0]}-{post_covid_years[1]})", post_covid_years),
    ]
    for period_name, (start, end) in periods:
        for borough in boroughs:
            sub = trend_pivot.loc[start:end, borough]
            growth_pct, r2, p_value = _growth(sub)
            rows.append(
                {
                    "period": period_name,
                    "borough": borough,
                    "annual_growth_pct": growth_pct,
                    "r_squared": r2,
                    "p_value": p_value,
                    "significant": bool(p_value < 0.05),
                }
            )
    result = pd.DataFrame(rows)
    logger.info("Q2: growth rates computed for %d period x borough combos", len(result))
    return result


def find_growth_crossover(
    trend_pivot: pd.DataFrame,
    leader_a: str = "Manhattan",
    leader_b: str = "Brooklyn",
    covid_year: int = COVID_YEAR,
) -> dict:
    """Find when the review-volume leader switched between two boroughs.
    두 자치구 간 리뷰 건수 리더가 바뀐 시점을 찾는다.

    Args:
        trend_pivot: Output of `analyze_borough_review_trend()`.
        leader_a: First borough to compare (e.g. "Manhattan").
        leader_b: Second borough to compare (e.g. "Brooklyn").
        covid_year: Year used to split "recent" resurgence from history.

    Returns:
        Dict with keys `b_leads_from`, `b_leads_until` (years `leader_b` led),
        `a_reclaims_from` (year `leader_a` regained the lead at/after
        `covid_year`), and `latest_gap` (gap in the most recent year).
        Any key is `None` if no such period exists in the data.
        `b_leads_from`, `b_leads_until`, `a_reclaims_from`, `latest_gap` 키를
        가진 dict. 해당 구간이 없으면 값은 `None`.
    """
    gap = trend_pivot[leader_a] - trend_pivot[leader_b]
    b_leads = gap[gap < 0]
    a_leads_recent = gap[(gap.index >= covid_year) & (gap > 0)]

    return {
        "b_leads_from": int(b_leads.index.min()) if len(b_leads) else None,
        "b_leads_until": int(b_leads.index.max()) if len(b_leads) else None,
        "a_reclaims_from": int(a_leads_recent.index.min())
        if len(a_leads_recent)
        else None,
        "latest_gap": float(gap.iloc[-1]),
    }


# ---------------------------------------------------------------------------
# Q3 — Risk Distribution / 리스크 분포
# ---------------------------------------------------------------------------


def analyze_license_risk_distribution(conn: sqlite3.Connection) -> pd.DataFrame:
    """Distribution of license status by borough, for registration-eligible listings.
    등록 대상 매물의 자치구별 라이선스 상태 분포.

    [Distribution via Subquery/CTE] `WITH eligible_listings` CTE filter
    (`minimum_nights < 30`) applied BEFORE the GROUP BY, so the distribution
    only describes listings the registration law actually governs.
    `WITH eligible_listings` CTE로 GROUP BY 전에 (`minimum_nights < 30`)를
    먼저 필터링해, 등록법이 실제로 적용되는 매물만을 대상으로 분포를 계산한다.

    So-what: Quantifies how much of Q1's revenue map sits with hosts who are
    not legally registered — the compliance/regulatory-risk exposure.
    so-what: Q1의 매출 지도 중 얼마가 법적으로 미등록된 호스트에게 있는지
    정량화한다 — 컴플라이언스/규제 리스크 노출도.

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.

    Returns:
        DataFrame with columns [borough, license_status, listing_count,
        total_revenue].
        [borough, license_status, listing_count, total_revenue] 컬럼의 DataFrame.
    """
    query = f"""
    WITH eligible_listings AS (
        SELECT *
        FROM listings
        WHERE minimum_nights < {REGISTRATION_MIN_NIGHTS_THRESHOLD}
    )
    SELECT
        neighbourhood_group_cleansed AS borough,
        CASE
            WHEN license IS NULL   THEN 'Unlicensed'
            WHEN license = 'Exempt' THEN 'Exempt'
            ELSE 'Licensed'
        END AS license_status,
        COUNT(*)                                        AS listing_count,
        SUM(COALESCE(estimated_revenue_l365d, 0))       AS total_revenue
    FROM eligible_listings
    GROUP BY borough, license_status
    ORDER BY borough, license_status
    """
    risk = pd.read_sql(query, conn)
    logger.info("Q3: risk distribution computed — %d borough x status rows", len(risk))
    return risk


def summarize_revenue_at_risk(risk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize revenue/listing share by license status, overall and by borough.
    전체 및 자치구별로 라이선스 상태별 매출/매물 비중을 요약한다.

    Args:
        risk: Output of `analyze_license_risk_distribution()`.

    Returns:
        Tuple of:
        - `overall`: one row per license_status with listing/revenue totals
          and their share of all eligible listings.
        - `unlicensed_by_borough`: Unlicensed-only rows with each borough's
          share of all unlicensed listings, sorted by listing_count descending.
        다음 두 개로 구성된 튜플:
        - `overall`: license_status별 매물/매출 합계 및 전체 대비 비중.
        - `unlicensed_by_borough`: 미등록 매물만, 전체 미등록 대비 자치구별
          비중, listing_count 내림차순 정렬.
    """
    overall = risk.groupby("license_status")[["listing_count", "total_revenue"]].sum()
    overall["listing_share_pct"] = (
        overall["listing_count"] / overall["listing_count"].sum() * 100
    ).round(1)
    overall["revenue_share_pct"] = (
        overall["total_revenue"] / overall["total_revenue"].sum() * 100
    ).round(1)

    unlicensed = risk[risk["license_status"] == "Unlicensed"].copy()
    unlicensed["share_of_all_unlicensed_pct"] = (
        unlicensed["listing_count"] / unlicensed["listing_count"].sum() * 100
    ).round(1)
    unlicensed = unlicensed.sort_values("listing_count", ascending=False)

    logger.info(
        "Q3: %d unlicensed listings across %d boroughs",
        unlicensed["listing_count"].sum(),
        len(unlicensed),
    )
    return overall, unlicensed


def check_license_borough_independence(risk: pd.DataFrame) -> dict:
    """Chi-square test of independence: is license status independent of borough?
    카이제곱 독립성 검정: 라이선스 상태는 자치구와 독립인가?

    Args:
        risk: Output of `analyze_license_risk_distribution()`.

    Returns:
        Dict with keys `chi2`, `dof`, `p_value`, `significant` (p < 0.05).
        `chi2`, `dof`, `p_value`, `significant`(p < 0.05) 키를 가진 dict.
    """
    contingency = risk.pivot(
        index="borough", columns="license_status", values="listing_count"
    ).fillna(0)
    chi2, p_value, dof, _expected = stats.chi2_contingency(contingency)
    logger.info("Q3: chi2=%.1f, dof=%d, p=%.2e", chi2, dof, p_value)
    return {
        "chi2": float(chi2),
        "dof": int(dof),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05),
    }


# ---------------------------------------------------------------------------
# Q4 — Priority Ranking / 우선순위 랭킹
# ---------------------------------------------------------------------------


def analyze_host_priority_ranking(conn: sqlite3.Connection) -> pd.DataFrame:
    """Rank unlicensed hosts by at-risk revenue with a cumulative share.
    미등록 호스트를 리스크 매출 기준으로 순위 매기고 누적 비중을 계산한다.

    [Advanced Comparison] `RANK() OVER (...)` + cumulative `SUM() OVER (...)`
    window functions, built on the Q3 CTE-filtered unlicensed subset.
    Q3의 CTE 필터링된 미등록 서브셋 위에 `RANK() OVER (...)`와 누적
    `SUM() OVER (...)` 윈도우 함수를 적용한다.

    So-what: Turns the aggregate risk from Q3 into an actionable, ranked
    outreach list — who should compliance contact first?
    so-what: Q3의 집계된 리스크를 실행 가능한 우선순위 접촉 목록으로
    전환한다 — 컴플라이언스는 누구부터 접촉해야 하는가?

    Args:
        conn: SQLite connection to `airbnb_nyc.sqlite`.

    Returns:
        DataFrame with columns [host_id, listing_count, host_revenue,
        revenue_rank, cumulative_revenue, cumulative_pct], sorted by rank.
        [host_id, listing_count, host_revenue, revenue_rank,
        cumulative_revenue, cumulative_pct] 컬럼의 DataFrame. 순위순 정렬.
    """
    query = f"""
    WITH eligible_listings AS (
        SELECT * FROM listings WHERE minimum_nights < {REGISTRATION_MIN_NIGHTS_THRESHOLD}
    ),
    unlicensed_listings AS (
        SELECT * FROM eligible_listings WHERE license IS NULL
    ),
    host_revenue AS (
        SELECT
            host_id,
            COUNT(*)                                  AS listing_count,
            SUM(COALESCE(estimated_revenue_l365d, 0)) AS host_revenue
        FROM unlicensed_listings
        GROUP BY host_id
    )
    SELECT
        host_id,
        listing_count,
        host_revenue,
        RANK() OVER (ORDER BY host_revenue DESC)                          AS revenue_rank,
        SUM(host_revenue) OVER (
            ORDER BY host_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                                 AS cumulative_revenue,
        ROUND(
            SUM(host_revenue) OVER (
                ORDER BY host_revenue DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) * 100.0 / SUM(host_revenue) OVER (), 2
        )                                                                 AS cumulative_pct
    FROM host_revenue
    ORDER BY revenue_rank
    """
    host_rank = pd.read_sql(query, conn)
    logger.info(
        "Q4: %d at-risk hosts ranked, total at-risk revenue $%.0f",
        len(host_rank),
        host_rank["host_revenue"].sum(),
    )
    return host_rank


def hosts_needed_for_target(host_rank: pd.DataFrame, target_pct: float) -> int:
    """Number of top hosts needed for cumulative revenue to reach a target %.
    누적 매출이 목표 %에 도달하는 데 필요한 상위 호스트 수.

    Args:
        host_rank: Output of `analyze_host_priority_ranking()`.
        target_pct: Target cumulative revenue percentage (e.g. 50 or 80).

    Returns:
        Number of top-ranked hosts required to reach `target_pct`.
        `target_pct`에 도달하는 데 필요한 상위 호스트 수.
    """
    return int((host_rank["cumulative_pct"] >= target_pct).idxmax()) + 1


def gini_coefficient(values: np.ndarray | pd.Series) -> float:
    """Compute the Gini coefficient of a distribution (0 = equal, 1 = maximal inequality).
    분포의 지니계수를 계산한다 (0 = 완전 평등, 1 = 최대 불평등).

    Args:
        values: Array-like of non-negative values (e.g. revenue per host).

    Returns:
        Gini coefficient as a float in [0, 1].
        [0, 1] 범위의 지니계수.
    """
    sorted_vals = np.sort(np.asarray(values))
    n = len(sorted_vals)
    cumulative = np.cumsum(sorted_vals)
    return (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n
