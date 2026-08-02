"""Data cleaning — listings preparation only.
데이터 정제 — listings 전처리 전용.

All cleaning rules are derived from EDA findings in
notebooks/airbnb_business_eda.ipynb (Section 8 — Final Cleaning Decisions).
모든 정제 규칙은 notebooks/airbnb_business_eda.ipynb 8번 섹션(최종 전처리 계획)에서
도출됐다.

Each transformation includes a WHY comment explaining the business/data reason.
모든 변환에는 WHY 주석으로 이유를 설명한다.

Public API
----------
clean(df)                 -> df_clean : adds license_status + is_active, safe for all questions
get_eligible_listings(df) -> df       : Q3/Q4-only subset (minimum_nights < 30)
drop_null_revenue(df)     -> df       : Q1/Q3/Q4-only filter for revenue-based analysis
"""

from __future__ import annotations

import logging

import pandas as pd

from pipeline.constants import REGISTRATION_MIN_NIGHTS_THRESHOLD

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual cleaning steps (private)
# 개별 정제 단계 (내부 함수)
# ---------------------------------------------------------------------------


def _add_license_status(df: pd.DataFrame) -> pd.DataFrame:
    """Derive a 3-way `license_status` column from the raw `license` field.
    원본 `license` 컬럼에서 3단계 `license_status` 컬럼을 파생한다.

    WHY: `license` has 3 real states — NULL (unlicensed), the literal string
    'Exempt' (legally exempt, e.g. a hotel or a host who never needed to
    register), or an actual registration number (licensed). Collapsing this
    to a 2-way flag would misclassify legally-exempt listings as "at risk",
    overstating the compliance problem.
    `license`는 NULL(미등록), 문자열 'Exempt'(법적 면제), 등록번호(등록됨)의
    3가지 실제 상태를 가진다. 2단계로 합치면 법적으로 면제된 매물까지
    "리스크"로 분류되어 컴플라이언스 문제를 과대평가하게 된다.
    """
    df = df.copy()
    df["license_status"] = df["license"].apply(
        lambda v: "Unlicensed" if pd.isna(v) else ("Exempt" if v == "Exempt" else "Licensed")
    )
    logger.debug(
        "add_license_status: %s", df["license_status"].value_counts().to_dict()
    )
    return df


def _add_is_active_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Derive an `is_active` flag from `estimated_revenue_l365d`.
    `estimated_revenue_l365d`에서 `is_active` 플래그를 파생한다.

    WHY: ~55% of listings with a non-null revenue value report exactly $0 —
    a real "no bookings in the last 12 months" signal, not missing data.
    Flagging it explicitly (instead of silently averaging it into segment
    revenue) lets downstream analysis report both a realistic "active host"
    average and an honest active rate.
    매출이 결측이 아닌 매물의 약 55%가 정확히 $0을 기록한다 — 결측이 아니라
    "최근 1년간 예약 없음"이라는 실제 신호다. 이를 명시적으로 플래그하면
    세그먼트 평균에 조용히 섞이는 대신, 활성 호스트의 현실적인 평균과
    정직한 활성 비율을 함께 보고할 수 있다.

    Rows with NULL revenue (Airbnb could not compute it at all) are left as
    NA rather than coerced to False, since "not computable" is not the same
    as "inactive".
    매출 자체가 결측(계산 불가)인 행은 False가 아니라 NA로 유지한다.
    "계산 불가"와 "비활성"은 다른 의미이기 때문이다.
    """
    df = df.copy()
    df["is_active"] = df["estimated_revenue_l365d"].apply(
        lambda v: pd.NA if pd.isna(v) else bool(v > 0)
    )
    return df


# ---------------------------------------------------------------------------
# Public API
# 공개 API
# ---------------------------------------------------------------------------


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply global derived-column rules to the raw `listings` DataFrame.
    원본 `listings` DataFrame에 전역 파생 컬럼 규칙을 적용한다.

    Rules applied (see EDA Section 8-1):
        1. Derive `license_status` (Unlicensed / Exempt / Licensed).
        2. Derive `is_active` from `estimated_revenue_l365d`.
    적용 규칙 (EDA 8-1 섹션 참조):
        1. `license_status` 파생 (Unlicensed / Exempt / Licensed).
        2. `estimated_revenue_l365d` 기반 `is_active` 파생.

    Rows with NULL revenue are intentionally retained here — dropping them is
    analysis-specific (only needed for revenue-based questions) and is left to
    `drop_null_revenue()` so that non-revenue analyses (e.g. license-status
    counts) are not silently shrunk.
    매출 결측 행은 여기서 의도적으로 유지한다. 제거는 매출 기반 분석에서만
    필요하므로 `drop_null_revenue()`에 위임한다 — 그래야 매출과 무관한 분석
    (예: 라이선스 상태 집계)이 불필요하게 줄어들지 않는다.

    Args:
        df: Raw listings DataFrame from `load.load_raw(path, "listings")`.
            `load.load_raw(path, "listings")` 출력 원본 DataFrame.

    Returns:
        Listings DataFrame with `license_status` and `is_active` added.
        `license_status`와 `is_active`가 추가된 listings DataFrame.
    """
    logger.info("Starting cleaning pipeline — %d input rows", len(df))
    df = _add_license_status(df)
    df = _add_is_active_flag(df)
    logger.info("Cleaning complete — %d rows, %d columns", *df.shape)
    return df


def get_eligible_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Return only listings legally subject to short-term-rental registration.
    단기 임대 등록법이 실제로 적용되는 매물만 반환한다.

    WHY: Only ~18.3% of listings have `minimum_nights < 30`; the rest are
    already configured as 30+ night stays and are exempt from NYC Local Law
    18 by design. Computing license-risk metrics over the full listings table
    would understate the real compliance rate for the population the law
    actually governs.
    `minimum_nights < 30`인 매물은 전체의 약 18.3%뿐이며, 나머지는 이미
    30박 이상으로 설정되어 설계상 NYC Local Law 18 적용 대상이 아니다.
    전체 매물을 기준으로 라이선스 리스크를 계산하면, 법이 실제로 적용되는
    대상의 준수율을 왜곡하게 된다.

    Args:
        df: Cleaned listings DataFrame (output of `clean()`), or raw listings.
            `clean()` 출력 또는 원본 listings DataFrame.

    Returns:
        Subset of `df` where `minimum_nights < 30`.
        `minimum_nights < 30`인 `df`의 서브셋.
    """
    before = len(df)
    eligible = df[df["minimum_nights"] < REGISTRATION_MIN_NIGHTS_THRESHOLD].copy()
    logger.info(
        "get_eligible_listings: %d -> %d rows (%.1f%% eligible)",
        before,
        len(eligible),
        len(eligible) / before * 100 if before else 0.0,
    )
    return eligible


def drop_null_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where Airbnb could not compute `estimated_revenue_l365d`.
    Airbnb가 `estimated_revenue_l365d`를 계산하지 못한 행을 제거한다.

    WHY: 30.9% of listings have a NULL revenue value — Airbnb simply could
    not estimate it (not the same as $0, which means "computed, and it was
    zero"). Any revenue-based aggregate (sum, average, ranking) must exclude
    these rows or it will silently treat "unknown" as if it doesn't exist.
    전체 매물의 30.9%는 매출이 NULL이다 — Airbnb가 아예 계산하지 못했다는 뜻이며
    "계산됐고 값이 0"인 것과는 다르다. 매출 기반 집계(합계, 평균, 순위)는
    반드시 이 행들을 제외해야 하며, 그렇지 않으면 "알 수 없음"을 존재하지
    않는 것처럼 조용히 처리하게 된다.

    Args:
        df: Listings DataFrame (raw or cleaned).
            listings DataFrame (원본 또는 정제됨).

    Returns:
        Subset of `df` where `estimated_revenue_l365d` is not null.
        `estimated_revenue_l365d`가 결측이 아닌 `df`의 서브셋.
    """
    before = len(df)
    out = df[df["estimated_revenue_l365d"].notna()].copy()
    logger.info(
        "drop_null_revenue: %d -> %d rows (%d dropped)",
        before,
        len(out),
        before - len(out),
    )
    return out
