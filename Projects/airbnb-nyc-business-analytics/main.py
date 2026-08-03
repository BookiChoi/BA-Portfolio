"""Entry point for the Airbnb NYC Business Analytics pipeline.
Airbnb NYC 비즈니스 분석 파이프라인 진입점.

Full pipeline:

    Load → Clean → Analyze → Visualize → Save

Run from the project directory:

    python main.py
    python main.py --data data/airbnb_nyc.sqlite --output outputs/

This file contains no business logic — it only orchestrates
the building blocks in ``pipeline/``.
이 파일에는 비즈니스 로직이 없다.
``pipeline/`` 패키지의 빌딩 블록을 연결(orchestrate)하는 역할만 한다.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.analyze import (
    analyze_borough_review_trend,
    analyze_growth_rates,
    analyze_host_priority_ranking,
    analyze_license_risk_distribution,
    analyze_market_segmentation,
    analyze_superhost_effect,
    check_borough_revenue_difference,
    check_license_borough_independence,
    find_growth_crossover,
    gini_coefficient,
    hosts_needed_for_target,
    summarize_revenue_at_risk,
)
from pipeline.clean import clean, drop_null_revenue
from pipeline.load import get_connection, load_raw
from pipeline.visualize import (
    plot_borough_review_trend,
    plot_growth_rate_comparison,
    plot_license_status_share,
    plot_pareto_curve,
    plot_segment_revenue,
    plot_superhost_effect,
    plot_top_priority_hosts,
    plot_unlicensed_by_borough,
)

# ---------------------------------------------------------------------------
# Defaults / 기본값
# ---------------------------------------------------------------------------
DATA_PATH = Path("data/airbnb_nyc.sqlite")
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
        data_path:   SQLite 데이터베이스 파일 경로 (``airbnb_nyc.sqlite``).
        outputs_dir: 차트와 요약 CSV를 저장할 디렉토리.
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load / 데이터 로드
    # ------------------------------------------------------------------
    logger.info("── LOAD ──────────────────────────────────────")
    listings_raw = load_raw(data_path, "listings")
    logger.info("Loaded listings: %d rows x %d columns", *listings_raw.shape)

    # ------------------------------------------------------------------
    # 2. Clean / 데이터 정제
    #    listings_clean is a checkpoint only — Q1-Q4 below re-query the raw
    #    SQLite tables directly and re-apply the same filters in SQL, so this
    #    step's output is not passed downstream. It exists to validate that
    #    clean.py's rules run cleanly against the real data (see row counts
    #    in the log) and to keep `pipeline/clean.py` covered end-to-end.
    #    listings_clean은 검증용 체크포인트일 뿐이다 — 아래 Q1~Q4는 원본
    #    SQLite 테이블을 직접 다시 읽고 동일한 필터를 SQL에서 다시 적용하므로,
    #    이 단계의 출력은 이후로 전달되지 않는다. clean.py의 규칙이 실제
    #    데이터에서 문제없이 동작하는지(로그의 행 수 변화로 확인) 검증하고,
    #    `pipeline/clean.py`가 end-to-end로 실행되도록 하기 위한 단계다.
    # ------------------------------------------------------------------
    logger.info("── CLEAN ─────────────────────────────────────")
    listings_clean = clean(listings_raw)
    listings_revenue_ready = drop_null_revenue(listings_clean)
    logger.info(
        "Clean checkpoint — %d raw -> %d cleaned -> %d with usable revenue",
        len(listings_raw),
        len(listings_clean),
        len(listings_revenue_ready),
    )

    # ------------------------------------------------------------------
    # 3. Analyze / 분석
    #    Q1-Q4 are SQL-backed (JOIN, GROUP BY, CTE, window functions) and
    #    run directly against the SQLite connection, mirroring the EDA notebook.
    #    Q1~Q4는 SQL 기반(JOIN, GROUP BY, CTE, 윈도우 함수)이며 EDA 노트북과
    #    동일하게 SQLite connection에 직접 실행한다.
    # ------------------------------------------------------------------
    logger.info("── ANALYZE ───────────────────────────────────")

    with get_connection(data_path) as conn:
        # Q1 — Market Segmentation / 시장 세분화
        segment = analyze_market_segmentation(conn)
        superhost_effect = analyze_superhost_effect(conn)
        borough_test = check_borough_revenue_difference(conn)
        logger.info(
            "Q1 done — top segment: %s / %s (%.1f%% of revenue); "
            "borough effect significant=%s (p=%.2e)",
            segment.iloc[0]["borough"],
            segment.iloc[0]["room_type"],
            segment.iloc[0]["revenue_share_pct"],
            borough_test["significant"],
            borough_test["p_value"],
        )

        # Q2 — Growth Trend / 성장 추이
        trend_pivot = analyze_borough_review_trend(conn)
        growth_df = analyze_growth_rates(trend_pivot)
        crossover = find_growth_crossover(trend_pivot)
        logger.info(
            "Q2 done — %d years tracked; Brooklyn led %s-%s, Manhattan reclaimed from %s",
            len(trend_pivot),
            crossover["b_leads_from"],
            crossover["b_leads_until"],
            crossover["a_reclaims_from"],
        )

        # Q3 — Risk Distribution / 리스크 분포
        risk = analyze_license_risk_distribution(conn)
        overall_risk, unlicensed_by_borough = summarize_revenue_at_risk(risk)
        independence_test = check_license_borough_independence(risk)
        logger.info(
            "Q3 done — unlicensed revenue share %.1f%%; independence significant=%s (p=%.2e)",
            overall_risk.loc["Unlicensed", "revenue_share_pct"],
            independence_test["significant"],
            independence_test["p_value"],
        )

        # Q4 — Priority Ranking / 우선순위 랭킹
        host_rank = analyze_host_priority_ranking(conn)
        n_50 = hosts_needed_for_target(host_rank, 50)
        n_80 = hosts_needed_for_target(host_rank, 80)
        gini = gini_coefficient(host_rank["host_revenue"].values)
        logger.info(
            "Q4 done — %d at-risk hosts; top %d hosts = 50%% of revenue, "
            "top %d hosts = 80%% (Gini=%.3f)",
            len(host_rank),
            n_50,
            n_80,
            gini,
        )

    # ------------------------------------------------------------------
    # 4. Visualize & Save charts / 시각화 및 차트 저장
    # ------------------------------------------------------------------
    logger.info("── VISUALIZE ─────────────────────────────────")

    charts = {
        # Q1
        "q1_segment_revenue.png": plot_segment_revenue(segment),
        "q1_superhost_effect.png": plot_superhost_effect(superhost_effect),
        # Q2
        "q2_borough_review_trend.png": plot_borough_review_trend(trend_pivot),
        "q2_growth_rate_comparison.png": plot_growth_rate_comparison(growth_df),
        # Q3
        "q3_license_status_share.png": plot_license_status_share(risk),
        "q3_unlicensed_by_borough.png": plot_unlicensed_by_borough(unlicensed_by_borough),
        # Q4
        "q4_pareto_curve.png": plot_pareto_curve(host_rank, gini),
        "q4_top_priority_hosts.png": plot_top_priority_hosts(host_rank),
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
        "q1_segment_revenue.csv": segment,
        "q1_superhost_effect.csv": superhost_effect,
        "q2_borough_review_trend.csv": trend_pivot.reset_index(),
        "q2_growth_rates.csv": growth_df,
        "q3_license_risk_distribution.csv": risk,
        "q3_unlicensed_by_borough.csv": unlicensed_by_borough,
        "q4_host_priority_ranking.csv": host_rank,
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
    parser = argparse.ArgumentParser(
        description="Run the Airbnb NYC Business Analytics pipeline."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_PATH,
        help=f"SQLite 데이터베이스 파일 경로 (기본값: {DATA_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUTS_DIR,
        help=f"차트 및 CSV 저장 디렉토리 (기본값: {OUTPUTS_DIR})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(data_path=args.data, outputs_dir=args.output)
