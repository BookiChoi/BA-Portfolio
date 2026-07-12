"""Analytical functions — one function per business question.
분석 함수 — 비즈니스 질문당 함수 하나.

Rules:
- Accept a cleaned DataFrame and return a DataFrame or dict.
- No printing, no plotting, no side effects.
- Every function is independently unit-testable.
규칙:
- 정제된 DataFrame을 받아 DataFrame 또는 dict를 반환한다.
- 출력(print), 시각화(plot), 부작용(side effect) 없음.
- 모든 함수를 독립적으로 단위 테스트할 수 있다.

Business Questions / 비즈니스 질문
------------------
Q1  Which countries generate the most revenue?       / 어느 국가가 가장 많은 매출을 만드는가?
Q2  How has monthly revenue changed over time?       / 월별 매출은 어떻게 변해왔는가?
Q3  Which products drive the most revenue?           / 어떤 상품이 매출을 주도하는가?
Q4  How are customer order values distributed?       / 고객 주문 금액 분포는 어떻게 되는가?
Q5  Who are the highest-value customers?             / 가장 가치 있는 고객은 누구인가?
"""

from __future__ import annotations

import logging

import pandas as pd

from pipeline.clean import remove_non_product_descriptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Q1 — Market Analysis / 시장 분석
# ---------------------------------------------------------------------------

def analyze_uk_vs_others(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue split: United Kingdom vs all other countries combined.
    UK vs 기타 국가 합계 매출 비중을 집계한다 (도넛 차트용).

    Args:
        df: Cleaned DataFrame from clean.clean().
            clean.clean() 출력 DataFrame.

    Returns:
        DataFrame with columns [Label, Revenue] — 2 rows: UK / Other Countries.
        [Label, Revenue] 컬럼의 DataFrame (2행: UK / Other Countries).
    """
    total  = df["Revenue"].sum()
    uk     = df[df["Country"] == "United Kingdom"]["Revenue"].sum()
    others = total - uk
    return pd.DataFrame({
        "Label":   ["United Kingdom", "Other Countries"],
        "Revenue": [uk, others],
    })


def analyze_country_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue by country (UK excluded), all countries returned.
    국가별 매출을 집계하고 전체 국가를 반환한다 (UK 제외).

    UK is excluded because it accounts for ~85% of total revenue and
    visually overwhelms all other countries in charts, making non-UK
    market patterns unreadable. Use analyze_uk_vs_others() for the
    full UK vs Others comparison.
    UK는 전체 매출의 ~85%를 차지해 포함 시 다른 국가들이 차트에서 보이지 않는다.
    UK vs Others 전체 비교는 analyze_uk_vs_others()를 사용할 것.

    Note: RevenueShare_pct is calculated against the full dataset total
    (including UK), so shares reflect the true business proportion.
    RevenueShare_pct는 UK 포함 전체 매출 대비 비중으로 계산된다.

    Args:
        df: Cleaned DataFrame from clean.clean().
            clean.clean() 출력 DataFrame.

    Returns:
        DataFrame with columns [Country, Revenue, RevenueShare_pct],
        sorted by Revenue descending, United Kingdom excluded.
        [Country, Revenue, RevenueShare_pct] 컬럼의 DataFrame. Revenue 내림차순 정렬. UK 제외.
    """
    total = df["Revenue"].sum()   # full-dataset total including UK / UK 포함 전체 매출
    result = (
        df[df["Country"] != "United Kingdom"]
        .groupby("Country")["Revenue"]
        .sum()
        .reset_index(name="Revenue")
        .sort_values("Revenue", ascending=False)
    )
    result["RevenueShare_pct"] = (result["Revenue"] / total * 100).round(2)
    logger.info("Q1: %d non-UK countries computed", len(result))
    return result


# ---------------------------------------------------------------------------
# Q2 — Sales Trend Analysis / 추세 분석
# ---------------------------------------------------------------------------

def analyze_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue by calendar month.
    월별 매출을 집계한다.

    Note: December 2011 contains only 9 days of data. Rows are retained but the
    partial month should be flagged in visualisations.
    참고: 2011년 12월은 9일치 데이터만 존재한다. 행은 유지하되 시각화에서 부분 월임을 표시해야 한다.

    Args:
        df: Cleaned DataFrame with an InvoiceDate column.
            InvoiceDate 컬럼이 있는 정제된 DataFrame.

    Returns:
        DataFrame with columns [YearMonth (Period), Revenue], sorted chronologically.
        [YearMonth (Period), Revenue] 컬럼의 DataFrame. 시간순 정렬.
    """
    result = (
        df.assign(YearMonth=df["InvoiceDate"].dt.to_period("M"))
        .groupby("YearMonth")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("YearMonth")
    )
    logger.info("Q2: %d months of revenue data", len(result))
    return result
