"""Data cleaning pipeline.
데이터 정제 파이프라인.

All cleaning rules are derived from EDA findings in notebooks/business_eda.ipynb.
모든 정제 규칙은 notebooks/business_eda.ipynb의 EDA 결과에서 도출됐다.

Each rule is a small, focused function with a WHY comment explaining the
business/data reason for the transformation.
각 규칙은 작고 단일 목적의 함수이며, 변환 이유를 WHY 주석으로 설명한다.

Public API
----------
clean(df)                        -> df_clean  : global filters, safe for Q1–Q4
get_customer_df(df_clean)        -> cust_df   : Q5-only subset (CustomerID required)
remove_non_product_descriptions  -> df        : Q3-only filter
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Non-product Description values identified during Q3 EDA (top-revenue list inspection).
# Internal charges, shipping fees, and accounting entries — not sellable items.
# Q3 EDA에서 상위 매출 목록 검토 중 발견된 비상품 Description 값들.
NON_PRODUCT_DESC: frozenset[str] = frozenset({
    "DOTCOM POSTAGE",
    "POSTAGE",
    "CARRIAGE",
    "Manual",
    "AMAZON FEE",
    "Adjust bad debt",
})


# ---------------------------------------------------------------------------
# Individual cleaning steps (private)
# 개별 정제 단계 (내부 함수)
# ---------------------------------------------------------------------------

def _remove_non_positive_quantity(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where Quantity <= 0.
    Quantity가 0 이하인 행을 제거한다.

    WHY: Negative quantities represent cancellation/return rows (InvoiceNo starts
    with 'C'). Zero-quantity rows carry no revenue and are noise. Retaining them
    would double-count cancelled transactions in revenue totals.
    음수 Quantity는 취소/반품 행을 나타낸다. 0인 행은 매출이 없는 노이즈다.
    유지하면 취소 거래가 매출 집계에서 이중 계산된다.
    """
    before = len(df)
    df = df[df["Quantity"] > 0]
    logger.debug("remove_non_positive_quantity: dropped %d rows", before - len(df))
    return df


def _remove_non_positive_price(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where UnitPrice <= 0.
    UnitPrice가 0 이하인 행을 제거한다.

    WHY: UnitPrice = 0 rows are stock-adjustment or internal records (often paired
    with missing CustomerID and unusual Descriptions such as 'amazon'). Two rows
    have a negative UnitPrice — data entry errors. Neither contributes meaningful
    revenue and both distort analysis.
    UnitPrice = 0인 행은 재고 조정 또는 내부 기록이다. 음수 UnitPrice 2건은
    데이터 입력 오류다. 둘 다 의미 있는 매출이 없고 분석을 왜곡한다.
    """
    before = len(df)
    df = df[df["UnitPrice"] > 0]
    logger.debug("remove_non_positive_price: dropped %d rows", before - len(df))
    return df


def _remove_non_sales_invoices(df: pd.DataFrame) -> pd.DataFrame:
    """Remove accounting journal entries identified by a letter-prefix InvoiceNo.
    알파벳 접두사 InvoiceNo로 식별되는 회계 분개 행을 제거한다.

    WHY: Three rows have InvoiceNo starting with 'A' (A563185–A563187),
    Description = 'Adjust bad debt', StockCode = 'B'. These are accounting
    write-offs, not real transactions. They survive the Quantity/UnitPrice filters
    (Quantity=1, UnitPrice=£11,062) and must be removed explicitly.
    C-prefix rows (cancellations) are already removed by the Quantity filter,
    so the regex targets every letter-prefix EXCEPT 'C'.
    A-prefix 인보이스 3건은 대손 상각 회계 처리 항목으로 실제 거래가 아니다.
    Quantity=1, UnitPrice=£11,062이라 현재 필터를 통과하므로 별도 제거가 필요하다.
    C-prefix 행은 Quantity 필터로 이미 제거되므로 정규식은 C를 제외한다.
    """
    before = len(df)
    mask = df["InvoiceNo"].astype(str).str.match(r"^[A-BD-Za-bd-z]")
    df = df[~mask]
    logger.debug("remove_non_sales_invoices: dropped %d rows", before - len(df))
    return df


def _create_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Add a Revenue column: Quantity x UnitPrice.
    Revenue 컬럼 추가: Quantity x UnitPrice.

    WHY: Revenue is not present in the raw dataset and is the primary metric
    for Q1-Q5. Creating it once here ensures every downstream function uses
    a consistent definition.
    Revenue는 원본 데이터셋에 없는 파생 컬럼이다. Q1~Q5의 핵심 지표이므로
    여기서 한 번만 생성해 모든 하위 함수에서 일관된 정의를 사용하도록 한다.
    """
    df = df.copy()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df


# ---------------------------------------------------------------------------
# Public API
# 공개 API
# ---------------------------------------------------------------------------

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all global cleaning rules and return a sales-ready DataFrame.
    전역 정제 규칙을 모두 적용하고 분석 준비된 DataFrame을 반환한다.

    Rules applied (see EDA Section 9-1):
        1. Remove Quantity <= 0  (cancellations / returns)
        2. Remove UnitPrice <= 0 (stock adjustments / data errors)
        3. Remove non-sales InvoiceNo prefixes (accounting entries)
        4. Create Revenue = Quantity x UnitPrice
    적용 규칙 (EDA 섹션 9-1 참조):
        1. Quantity <= 0 제거 (취소/반품)
        2. UnitPrice <= 0 제거 (재고 조정/데이터 오류)
        3. 비판매 InvoiceNo 접두사 제거 (회계 분개)
        4. Revenue = Quantity x UnitPrice 생성

    CustomerID NaN rows are intentionally retained — confirmed as guest purchases
    (EDA 8-2) and contribute to Q1-Q4 revenue. Use get_customer_df() to exclude them.
    CustomerID NaN 행은 의도적으로 유지된다. EDA 8-2에서 게스트 구매로 확인됐으며
    Q1~Q4 매출에 포함된다. Q5에서만 제외하려면 get_customer_df()를 사용할 것.

    Args:
        df: Raw DataFrame from load.load_raw().
            load.load_raw() 의 출력 원본 DataFrame.

    Returns:
        Cleaned DataFrame with a Revenue column added.
        Revenue 컬럼이 추가된 정제된 DataFrame.
    """
    logger.info("Starting cleaning pipeline — %d input rows", len(df))
    df = _remove_non_positive_quantity(df)
    df = _remove_non_positive_price(df)
    df = _remove_non_sales_invoices(df)
    df = _create_revenue(df)
    logger.info("Cleaning complete — %d rows remain", len(df))
    return df


def get_customer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a subset restricted to identified customers (CustomerID not NaN).
    CustomerID가 있는 행만 남긴 서브셋을 반환한다 (Q5 전용).

    WHY: ~25% of rows have no CustomerID (confirmed guest purchases in EDA 8-2).
    Q5 (customer value analysis) requires individual attribution, so anonymous rows
    must be excluded. This filter is NOT applied globally — guest transactions still
    count toward Q1-Q4 revenue totals.
    행의 약 25%는 CustomerID가 없다 (EDA 8-2에서 게스트 구매로 확인).
    Q5는 개인 고객 단위 집계가 필요하므로 익명 행을 제외해야 한다.
    이 필터는 전역 적용되지 않는다. 게스트 거래는 Q1~Q4 매출 합계에 포함된다.

    Args:
        df: Output of clean(). / clean() 의 출력.

    Returns:
        DataFrame with CustomerID NaN rows removed.
        CustomerID NaN 행이 제거된 DataFrame.
    """
    before = len(df)
    cust_df = df[df["CustomerID"].notna()].copy()
    logger.info(
        "get_customer_df: %d → %d rows (%d guest rows excluded)",
        before, len(cust_df), before - len(cust_df),
    )
    return cust_df


def remove_non_product_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Remove known non-product Description values (Q3 product analysis only).
    알려진 비상품 Description 값을 제거한다 (Q3 상품 분석 전용).

    WHY: The top-revenue product list (Q3 EDA) contains internal charges and fees
    (DOTCOM POSTAGE, POSTAGE, CARRIAGE, Manual, AMAZON FEE, Adjust bad debt).
    These inflate product revenue rankings and must be excluded before product-level
    analysis. They are NOT removed globally because they represent real revenue for
    the business as a whole.
    Q3 EDA 상위 매출 목록에 내부 수수료 및 배송비가 포함됐다. 이 항목들은 상품
    매출 순위를 왜곡하므로 상품 분석 전 제거해야 한다. 비즈니스 전체 매출 관점에서는
    실제 수익에 해당하므로 전역 제거하지 않는다.

    Args:
        df: Cleaned DataFrame (output of clean()). / clean() 의 출력.

    Returns:
        DataFrame with non-product rows removed.
        비상품 행이 제거된 DataFrame.
    """
    before = len(df)
    df = df[~df["Description"].isin(NON_PRODUCT_DESC)]
    logger.debug("remove_non_product_descriptions: dropped %d rows", before - len(df))
    return df
