"""Entry point for the Cornerstone Data Pipeline.
Cornerstone 데이터 파이프라인 진입점.

전체 파이프라인 실행:

    Load → Clean → Analyze → Visualize → Save

프로젝트 루트에서 실행:

    python main.py
    python main.py --data data/online_retail.xlsx --output outputs/

이 파일에는 비즈니스 로직이 없다.
pipeline/ 패키지의 빌딩 블록들을 연결(orchestrate)하는 역할만 한다.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.analyze import (
    analyze_country_revenue,
    analyze_customer_pareto,
    analyze_customer_value,
    analyze_large_order_impact,
    analyze_monthly_revenue,
    analyze_order_values,
    analyze_pareto,
    analyze_product_revenue,
    analyze_product_scatter,
    analyze_uk_vs_others,
    get_vip_ids,
)
from pipeline.clean import clean, get_customer_df
from pipeline.load import load_raw
from pipeline.visualize import (
    plot_country_revenue,
    plot_customer_revenue_histogram,
    plot_customer_segments,
    plot_monthly_revenue,
    plot_monthly_revenue_bar,
    plot_order_value_boxplot,
    plot_order_value_histogram,
    plot_pareto,
    plot_product_segments,
    plot_top_customers,
    plot_top_products,
    plot_uk_vs_others,
    plot_vip_seasonal,
)

# ---------------------------------------------------------------------------
# Defaults / 기본값
# ---------------------------------------------------------------------------
DATA_PATH   = Path("data/online_retail.xlsx")
OUTPUTS_DIR = Path("outputs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline / 파이프라인
# ---------------------------------------------------------------------------

def run_pipeline(data_path: Path = DATA_PATH, outputs_dir: Path = OUTPUTS_DIR) -> None:
    """Run the full Load → Clean → Analyze → Visualize pipeline.
    전체 Load → Clean → Analyze → Visualize 파이프라인을 실행한다.

    Args:
        data_path:   원본 데이터 파일 경로 (.xlsx 또는 .csv).
        outputs_dir: 차트와 요약 CSV를 저장할 디렉토리.
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load / 데이터 로드
    # ------------------------------------------------------------------
    logger.info("── LOAD ──────────────────────────────────────")
    df_raw = load_raw(data_path)

    # ------------------------------------------------------------------
    # 2. Clean / 데이터 정제
    # ------------------------------------------------------------------
    logger.info("── CLEAN ─────────────────────────────────────")
    df_clean = clean(df_raw)
    # Q5 전용 서브셋: CustomerID NaN 제외
    cust_df  = get_customer_df(df_clean)

    # ------------------------------------------------------------------
    # 3. Analyze / 분석
    # ------------------------------------------------------------------
    logger.info("── ANALYZE ───────────────────────────────────")

    # Q1 — 국가별 매출
    uk_vs_others    = analyze_uk_vs_others(df_clean)
    country_revenue = analyze_country_revenue(df_clean)
    logger.info("Q1 done — top country: %s", country_revenue.iloc[0]["Country"])

    # Q2 — 월별 매출 추이
    monthly_revenue = analyze_monthly_revenue(df_clean)
    logger.info("Q2 done — %d months", len(monthly_revenue))

    # Q3 — 상품 성과
    product_revenue  = analyze_product_revenue(df_clean, top_n=20)
    pareto           = analyze_pareto(df_clean)
    product_scatter  = analyze_product_scatter(df_clean)   # 4분면 산점도용
    logger.info("Q3 done — top product: %s", product_revenue.iloc[0]["Description"])

    # Q4 — 주문 금액 분포
    order_values       = analyze_order_values(df_clean)
    large_order_impact = analyze_large_order_impact(order_values)
    logger.info("Q4 done — %d unique orders, max £%s",
                len(order_values), f"{order_values['OrderValue'].max():,.0f}")

    # Q5 — 고객 가치 분석
    customer_value = analyze_customer_value(cust_df, top_n=20)
    cust_pareto    = analyze_customer_pareto(cust_df)
    vip_ids        = get_vip_ids(cust_df)                  # VIP vs Non-VIP 계절성 차트용
    # 4분면 차트 + 히스토그램용 전체 고객 프로파일 (상위 제한 없음)
    cust_profile = (
        cust_df.groupby("CustomerID")
        .agg(TotalRevenue=("Revenue", "sum"), OrderCount=("InvoiceNo", "nunique"))
        .reset_index()
    )
    logger.info(
        "Q5 done — top 20%% customers drive %.1f%% of revenue",
        cust_pareto["top_20pct_revenue_share"],
    )

    # ------------------------------------------------------------------
    # 4. Visualize & Save charts / 시각화 및 차트 저장
    # ------------------------------------------------------------------
    logger.info("── VISUALIZE ─────────────────────────────────")

    charts = {
        # Q1
        "q1_uk_vs_others.png":             plot_uk_vs_others(uk_vs_others),
        "q1_country_revenue.png":          plot_country_revenue(country_revenue),
        # Q2
        "q2_monthly_revenue.png":          plot_monthly_revenue(monthly_revenue),
        "q2_monthly_revenue_bar.png":      plot_monthly_revenue_bar(monthly_revenue),
        # Q3
        "q3_pareto.png":                   plot_pareto(pareto),
        "q3_top_products.png":             plot_top_products(product_revenue),
        "q3_product_segments.png":         plot_product_segments(product_scatter),
        # Q4
        "q4_order_value_histogram.png":    plot_order_value_histogram(order_values),
        "q4_order_value_boxplot.png":      plot_order_value_boxplot(order_values),
        # Q5
        "q5_top_customers.png":            plot_top_customers(customer_value),
        "q5_customer_segments.png":        plot_customer_segments(cust_profile),
        "q5_customer_revenue_hist.png":    plot_customer_revenue_histogram(cust_profile),
        "q5_vip_seasonal.png":             plot_vip_seasonal(cust_df, vip_ids),
    }
    for filename, fig in charts.items():
        path = outputs_dir / filename
        fig.savefig(path, dpi=150, bbox_inches="tight")
        fig.clf()
        logger.info("Saved → %s", path)

    # ------------------------------------------------------------------
    # 5. Save summary tables as CSV / 요약 테이블 CSV 저장
    # ------------------------------------------------------------------
    logger.info("── SAVE SUMMARIES ────────────────────────────")
    summary_tables = {
        "q1_country_revenue.csv":    country_revenue,
        "q2_monthly_revenue.csv":    monthly_revenue.assign(
                                         YearMonth=monthly_revenue["YearMonth"].astype(str)
                                     ),
        "q3_top_products.csv":       product_revenue,
        "q4_large_order_impact.csv": large_order_impact,
        "q5_top_customers.csv":      customer_value,
    }
    for filename, tbl in summary_tables.items():
        path = outputs_dir / filename
        tbl.to_csv(path, index=False)
        logger.info("Saved → %s", path)

    logger.info("── DONE ──────────────────────────────────────")
    logger.info("All outputs written to: %s", outputs_dir.resolve())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Cornerstone Data Pipeline.")
    parser.add_argument(
        "--data", type=Path, default=DATA_PATH,
        help=f"원본 데이터 파일 경로 (기본값: {DATA_PATH})",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUTS_DIR,
        help=f"차트 및 CSV 저장 디렉토리 (기본값: {OUTPUTS_DIR})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(data_path=args.data, outputs_dir=args.output)
