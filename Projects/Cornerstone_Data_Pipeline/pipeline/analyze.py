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
    total = df["Revenue"].sum()
    uk = df[df["Country"] == "United Kingdom"]["Revenue"].sum()
    others = total - uk
    return pd.DataFrame(
        {
            "Label": ["United Kingdom", "Other Countries"],
            "Revenue": [uk, others],
        }
    )


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
    total = df["Revenue"].sum()  # full-dataset total including UK / UK 포함 전체 매출
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


# ---------------------------------------------------------------------------
# Q3 — Product Performance / 상품 성과 분석
# ---------------------------------------------------------------------------


def analyze_product_revenue(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Return top N products by revenue with their frequency rank.
    매출 기준 상위 N 상품과 판매 빈도 순위를 반환한다.

    Non-product descriptions (postage, fees, etc.) are excluded before ranking.
    See clean.NON_PRODUCT_DESC for the exclusion list.
    비상품 Description(배송비, 수수료 등)은 순위 계산 전 제거된다.
    제외 목록은 clean.NON_PRODUCT_DESC 참조.

    Args:
        df:    Cleaned DataFrame.
               정제된 DataFrame.
        top_n: Number of top products to return.
               반환할 상위 상품 수.

    Returns:
        DataFrame with columns [Description, Revenue, FrequencyRank],
        sorted by Revenue descending.
        [Description, Revenue, FrequencyRank] 컬럼의 DataFrame. Revenue 내림차순 정렬.
    """
    df_prod = remove_non_product_descriptions(df)

    revenue = (
        df_prod.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .reset_index(name="Revenue")
    )

    # Frequency rank: 1 = most frequently ordered product
    # 빈도 순위: 1 = 가장 많이 주문된 상품
    freq = (
        df_prod.groupby("Description")
        .size()
        .rank(method="min", ascending=False)
        .astype(int)
    )

    logger.info("Q3: top %d products by revenue", top_n)

    return revenue.assign(FrequencyRank=lambda d: d["Description"].map(freq)).head(
        top_n
    )


def analyze_pareto(df: pd.DataFrame) -> pd.DataFrame:
    """Build a Pareto table to validate the 80/20 rule across all products.
    전 상품에 걸쳐 파레토 법칙(80/20)을 검증하기 위한 테이블을 생성한다.

    Args:
        df: Cleaned DataFrame.
            정제된 DataFrame.

    Returns:
        DataFrame with columns [Description, Revenue, cumulative_pct],
        sorted by Revenue descending, covering all products.
        [Description, Revenue, cumulative_pct] 컬럼의 DataFrame.
        Revenue 내림차순, 전 상품 포함.
    """
    df_prod = remove_non_product_descriptions(df)
    revenue = (
        df_prod.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .reset_index(name="Revenue")
    )
    total = revenue["Revenue"].sum()
    revenue["cumulative_pct"] = revenue["Revenue"].cumsum() / total * 100
    return revenue


def analyze_product_scatter(df: pd.DataFrame) -> pd.DataFrame:
    """Build product-level Revenue + Frequency table for the 4-quadrant scatter plot.
    4분면 산점도용 상품별 매출 + 판매 빈도 테이블을 생성한다.

    Args:
        df: Cleaned DataFrame.
            정제된 DataFrame.

    Returns:
        DataFrame with columns [Description, Revenue, Frequency].
        [Description, Revenue, Frequency] 컬럼의 DataFrame.
    """
    df_prod = remove_non_product_descriptions(df)
    result = (
        df_prod.groupby("Description")
        .agg(Revenue=("Revenue", "sum"), Frequency=("InvoiceNo", "count"))
        .reset_index()
    )
    return result


# ---------------------------------------------------------------------------
# Q4 — Customer Purchase Behaviour / 고객 구매 행동 분석
# ---------------------------------------------------------------------------


def analyze_order_values(df: pd.DataFrame) -> pd.DataFrame:
    """Compute total value per invoice (order).
    인보이스(주문)별 총 금액을 계산한다.

    Revenue is on a gross basis: cancellation invoices were already removed by
    clean.clean(), but the original orders they cancelled are retained.
    매출은 Gross 기준이다. 취소 인보이스는 clean.clean()에서 제거됐지만
    취소된 원본 주문은 유지된다.

    Args:
        df: Cleaned DataFrame.
            정제된 DataFrame.

    Returns:
        DataFrame with columns [InvoiceNo, OrderValue], sorted by OrderValue descending.
        [InvoiceNo, OrderValue] 컬럼의 DataFrame. OrderValue 내림차순 정렬.
    """
    result = (
        df.groupby("InvoiceNo")["Revenue"]
        .sum()
        .reset_index(name="OrderValue")
        .sort_values("OrderValue", ascending=False)
    )
    logger.info("Q4: %d unique invoices", len(result))
    return result


def analyze_large_order_impact(order_values: pd.DataFrame) -> pd.DataFrame:
    """Show how large orders affect order count share and revenue share.
    대형 주문이 주문 건수 비중과 매출 비중에 미치는 영향을 보여준다.

    Args:
        order_values: Output of analyze_order_values().
                      analyze_order_values() 의 출력.

    Returns:
        DataFrame with columns [Threshold, OrderCount, OrderPct, Revenue, RevenuePct].
        [Threshold, OrderCount, OrderPct, Revenue, RevenuePct] 컬럼의 DataFrame.
    """
    total_revenue = order_values["OrderValue"].sum()
    total_orders = len(order_values)
    rows = []
    for threshold in [500, 1_000, 5_000, 10_000]:
        large = order_values[order_values["OrderValue"] > threshold]
        rows.append(
            {
                "Threshold": threshold,
                "OrderCount": len(large),
                "OrderPct": round(len(large) / total_orders * 100, 2),
                "Revenue": round(large["OrderValue"].sum(), 2),
                "RevenuePct": round(large["OrderValue"].sum() / total_revenue * 100, 2),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Q5 — Customer Value Analysis / 고객 가치 분석
# ---------------------------------------------------------------------------


def analyze_customer_value(cust_df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Build a customer profile: revenue, order count, average order value.
    고객 프로파일을 생성한다: 총매출, 주문 수, 평균 주문 금액.

    Args:
        cust_df: CustomerID-filtered DataFrame from clean.get_customer_df().
                 clean.get_customer_df() 의 출력 (CustomerID NaN 제외된 DataFrame).
        top_n:   Number of top customers to return.
                 반환할 상위 고객 수.

    Returns:
        DataFrame with columns [CustomerID, TotalRevenue, OrderCount, AvgOrderValue],
        sorted by TotalRevenue descending.
        [CustomerID, TotalRevenue, OrderCount, AvgOrderValue] 컬럼의 DataFrame.
        TotalRevenue 내림차순 정렬.
    """
    revenue = (
        cust_df
        .groupby("CustomerID")["Revenue"]
        .sum()
        .reset_index(name="TotalRevenue")
    )
    # Unique invoice count per customer = actual number of orders placed
    # 고객별 고유 인보이스 수 = 실제 주문 횟수
    freq = (
        cust_df.groupby("CustomerID")["InvoiceNo"]
        .nunique()
        .reset_index(name="OrderCount")
    )
    result = (
        revenue.merge(freq, on="CustomerID")
        .assign(AvgOrderValue=lambda d: d["TotalRevenue"] / d["OrderCount"])
        .sort_values("TotalRevenue", ascending=False)
        .head(top_n)
    )
    logger.info("Q5: top %d customers computed", top_n)
    return result


def get_vip_ids(cust_df: pd.DataFrame) -> pd.Index:
    """Return CustomerIDs above median on BOTH revenue and frequency (VIP definition).
    매출과 구매 빈도가 둘 다 중앙값을 초과하는 고객 ID를 반환한다 (VIP 정의).

    Args:
        cust_df: CustomerID-filtered DataFrame.
                 CustomerID 필터링된 DataFrame.

    Returns:
        Series of VIP CustomerIDs.
        VIP CustomerID 배열.
    """
    profile = (
        cust_df.groupby("CustomerID")
        .agg(TotalRevenue=("Revenue", "sum"), OrderCount=("InvoiceNo", "nunique"))
        .reset_index()
    )
    rev_med = profile["TotalRevenue"].median()
    freq_med = profile["OrderCount"].median()
    vip = profile[
        (profile["TotalRevenue"] > rev_med) & (profile["OrderCount"] > freq_med)
    ]["CustomerID"]
    logger.info("VIP customers: %d (above median rev & freq)", len(vip))
    return vip


def analyze_customer_pareto(cust_df: pd.DataFrame) -> dict[str, float]:
    """Check whether the top 20% of customers drive ~80% of revenue (Pareto check).
    상위 20% 고객이 매출의 ~80%를 만드는지 확인한다 (파레토 검증).

    Args:
        cust_df: CustomerID-filtered DataFrame.
                 CustomerID 필터링된 DataFrame.

    Returns:
        Dict with keys: total_customers, top_20pct_n, top_20pct_revenue_share.
        total_customers, top_20pct_n, top_20pct_revenue_share 키를 가진 dict.
    """
    revenue = (
        cust_df
        .groupby("CustomerID")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )
    total_customers = len(revenue)
    top_n = max(1, int(total_customers * 0.20))
    top_share = revenue.iloc[:top_n].sum() / revenue.sum() * 100
    return {
        "total_customers": total_customers,
        "top_20pct_n": top_n,
        "top_20pct_revenue_share": round(top_share, 1),
    }
