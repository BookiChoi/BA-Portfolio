"""Visualization functions — one function per chart.
시각화 함수 — 차트당 함수 하나.

Rules:
- Accept an already-processed DataFrame (output of analyze functions).
- Return a matplotlib Figure object.
- Never call plt.show() — the caller decides whether to display or save.
- No analysis logic — that belongs in analyze.py.
규칙:
- 이미 처리된 DataFrame(analyze 함수의 출력)을 받는다.
- matplotlib Figure 객체를 반환한다.
- plt.show()를 절대 호출하지 않는다 — 호출자가 화면 출력 또는 저장을 결정한다.
- 분석 로직은 analyze.py에 있어야 한다.
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Q1 — Superhost Impact / 슈퍼호스트 영향
# ---------------------------------------------------------------------------


def visualize_superhost_impact(df: pd.DataFrame):
    """Plot superhost vs non-superhost revenue and occupancy comparison.
    슈퍼호스트 vs 비슈퍼호스트 매출·점유율 비교 차트.

    TODO: Implement chart.
    TODO: 차트 구현.

    Args:
        df: Output of ``analyze_superhost_impact``.
            ``analyze_superhost_impact`` 출력 DataFrame.
    """
    pass


# ---------------------------------------------------------------------------
# Q2 — Borough Growth Trend / 자치구 성장 추이
# ---------------------------------------------------------------------------


def visualize_borough_growth_trend(df: pd.DataFrame):
    """Plot borough-level new-activity growth trend over time.
    자치구별 신규 활동 증감 추이 차트.

    TODO: Implement chart.
    TODO: 차트 구현.

    Args:
        df: Output of ``analyze_borough_growth_trend``.
            ``analyze_borough_growth_trend`` 출력 DataFrame.
    """
    pass


# ---------------------------------------------------------------------------
# Q3 — Unlicensed Revenue Risk / 무허가 매출 리스크
# ---------------------------------------------------------------------------


def visualize_unlicensed_revenue_risk(df: pd.DataFrame):
    """Plot unlicensed revenue exposure by borough.
    자치구별 무허가 매출 노출 차트.

    TODO: Implement chart.
    TODO: 차트 구현.

    Args:
        df: Output of ``analyze_unlicensed_revenue_risk``.
            ``analyze_unlicensed_revenue_risk`` 출력 DataFrame.
    """
    pass


# ---------------------------------------------------------------------------
# Q4 — Host Revenue Concentration / 호스트 매출 집중도
# ---------------------------------------------------------------------------


def visualize_host_revenue_concentration(df: pd.DataFrame):
    """Plot cumulative revenue share for top hosts (Pareto-style).
    상위 호스트 누적 매출 비중 차트 (파레토 스타일).

    TODO: Implement chart.
    TODO: 차트 구현.

    Args:
        df: Output of ``analyze_host_revenue_concentration``.
            ``analyze_host_revenue_concentration`` 출력 DataFrame.
    """
    pass
