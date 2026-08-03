"""Visualization functions — one function per chart.
시각화 함수 — 차트당 함수 하나.

Rules:
- Accept an already-processed DataFrame (output of analyze functions).
- Return a matplotlib Figure object.
- Never call plt.show() — the caller decides whether to display or save.
- No analysis logic (groupby, filters, calculations) — that belongs in analyze.py.
규칙:
- 이미 처리된 DataFrame(analyze 함수의 출력)을 받는다.
- matplotlib Figure 객체를 반환한다.
- plt.show()를 절대 호출하지 않는다 — 호출자가 화면 출력 또는 저장을 결정한다.
- 분석 로직(groupby, 필터, 계산 등)은 analyze.py에 있어야 한다.
"""

from __future__ import annotations

import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Q1 — Market Segmentation Charts / 시장 세분화 차트
# ---------------------------------------------------------------------------


def plot_segment_revenue(segment: pd.DataFrame) -> matplotlib.figure.Figure:
    """Horizontal bar chart of revenue by borough x room-type segment.
    자치구 x 룸타입 세그먼트별 매출 가로 막대그래프 (상위 4개 강조).

    Args:
        segment: Output of `analyze.analyze_market_segmentation()`.
                 Required columns: [borough, room_type, total_revenue,
                 revenue_share_pct].

    Returns:
        matplotlib Figure.
    """
    plot_df = segment.copy()
    plot_df["label"] = plot_df["borough"] + " / " + plot_df["room_type"]
    plot_df = plot_df.sort_values("total_revenue", ascending=True)
    colors = [
        "#C44E52" if i >= len(plot_df) - 4 else "#94a3b8" for i in range(len(plot_df))
    ]

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.barh(plot_df["label"], plot_df["total_revenue"], color=colors)
    ax.set_xlabel("Total Estimated Revenue, Last 365 Days ($)")
    ax.set_title(
        "Q1 — Revenue by Borough x Room-Type Segment (Top 4 highlighted)",
        fontsize=13,
        fontweight="bold",
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:,.0f}M"))
    for i, v in enumerate(plot_df["total_revenue"]):
        ax.text(
            v * 1.01,
            i,
            f"{plot_df['revenue_share_pct'].iloc[i]:.1f}%",
            va="center",
            fontsize=8,
        )
    fig.tight_layout()
    return fig


def plot_superhost_effect(superhost_effect: pd.DataFrame) -> matplotlib.figure.Figure:
    """Grouped bar chart: superhost vs regular-host average revenue by segment.
    세그먼트별 슈퍼호스트 vs 일반 호스트 평균 매출 그룹 막대그래프.

    Args:
        superhost_effect: Output of `analyze.analyze_superhost_effect()`.
                          Required columns: [borough, room_type,
                          superhost_mean, regular_mean, lift_x].

    Returns:
        matplotlib Figure.
    """
    labels = superhost_effect["borough"] + "\n" + superhost_effect["room_type"]
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        x - width / 2,
        superhost_effect["regular_mean"],
        width,
        label="Regular host",
        color="#94a3b8",
    )
    ax.bar(
        x + width / 2,
        superhost_effect["superhost_mean"],
        width,
        label="Superhost",
        color="#C44E52",
    )
    for i, row in enumerate(superhost_effect.itertuples()):
        ax.text(
            i + width / 2,
            row.superhost_mean * 1.01,
            f"{row.lift_x:.1f}x",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Average Estimated Revenue, Last 365 Days ($)")
    ax.set_title(
        "Q1 — Superhost Revenue Lift in the Top Revenue Segments",
        fontsize=12,
        fontweight="bold",
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:,.0f}K"))
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q2 — Growth Trend Charts / 성장 추이 차트
# ---------------------------------------------------------------------------


def plot_borough_review_trend(
    trend_pivot: pd.DataFrame, covid_year: int = 2020, latest_year: int | None = None
) -> matplotlib.figure.Figure:
    """Line chart of yearly review counts by borough, with COVID/partial-year flags.
    자치구별 연도별 리뷰 수 라인 차트 (코로나·부분 연도 표시 포함).

    Args:
        trend_pivot: Output of `analyze.analyze_borough_review_trend()`.
        covid_year: Year to shade as the COVID dip.
        latest_year: Most recent (partial) year to shade; defaults to the
                     last index value in `trend_pivot`.

    Returns:
        matplotlib Figure.
    """
    if latest_year is None:
        latest_year = int(trend_pivot.index.max())

    fig, ax = plt.subplots(figsize=(13, 6))
    for borough in trend_pivot.columns:
        highlight = borough in ("Manhattan", "Brooklyn")
        style = "-o" if highlight else "--"
        lw = 2.5 if highlight else 1.2
        ax.plot(
            trend_pivot.index,
            trend_pivot[borough],
            style,
            linewidth=lw,
            label=borough,
            markersize=4,
        )

    ax.axvspan(covid_year - 0.1, covid_year + 0.5, color="gray", alpha=0.15)
    ax.text(
        covid_year,
        ax.get_ylim()[1] * 0.95,
        "COVID dip",
        ha="center",
        fontsize=9,
        color="gray",
    )
    ax.axvspan(latest_year - 0.5, latest_year + 0.5, color="orange", alpha=0.12)
    ax.text(
        latest_year,
        ax.get_ylim()[1] * 0.87,
        f"partial\n{latest_year}",
        ha="center",
        fontsize=8,
        color="darkorange",
    )

    ax.set_title(
        "Q2 — Yearly Review Count by Borough (Demand Proxy Over Time)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Review Count")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def plot_growth_rate_comparison(growth_df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Grouped bar chart of pre- vs post-COVID annual growth rate by borough.
    코로나 전후 자치구별 연평균 성장률 그룹 막대그래프.

    Args:
        growth_df: Output of `analyze.analyze_growth_rates()`.
                   Required columns: [period, borough, annual_growth_pct].

    Returns:
        matplotlib Figure.
    """
    pivot_growth = growth_df.pivot(
        index="period", columns="borough", values="annual_growth_pct"
    )
    # Keep chronological order (Pre-COVID first) regardless of groupby order.
    period_order = sorted(pivot_growth.index, key=lambda p: "Post" in p)
    pivot_growth = pivot_growth.loc[period_order]
    boroughs = list(pivot_growth.columns)

    x = np.arange(len(pivot_growth.index))
    width = 0.8 / max(len(boroughs), 1)
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

    fig, ax = plt.subplots(figsize=(9, 6))
    for i, borough in enumerate(boroughs):
        offset = (i - (len(boroughs) - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            pivot_growth[borough],
            width,
            label=borough,
            color=colors[i % len(colors)],
        )
        for bar, val in zip(bars, pivot_growth[borough]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + (1 if val >= 0 else -3),
                f"{val:.1f}%",
                ha="center",
                fontsize=10,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(pivot_growth.index)
    ax.set_ylabel("Annual Growth Rate (%, log-linear fit)")
    ax.set_title(
        "Q2 — Annual Growth Rate: Pre-COVID vs Post-COVID", fontsize=13, fontweight="bold"
    )
    ax.legend()
    ax.axhline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q3 — Risk Distribution Charts / 리스크 분포 차트
# ---------------------------------------------------------------------------


def plot_license_status_share(risk: pd.DataFrame) -> matplotlib.figure.Figure:
    """100%-stacked bar chart of license status share by borough.
    자치구별 라이선스 상태 100% 누적 막대 차트.

    Args:
        risk: Output of `analyze.analyze_license_risk_distribution()`.
              Required columns: [borough, license_status, listing_count].

    Returns:
        matplotlib Figure.
    """
    contingency = risk.pivot(
        index="borough", columns="license_status", values="listing_count"
    ).fillna(0)
    ordered_statuses = [
        s for s in ("Licensed", "Exempt", "Unlicensed") if s in contingency.columns
    ]
    share = contingency.div(contingency.sum(axis=1), axis=0) * 100
    share = share[ordered_statuses]
    share = share.loc[contingency.sum(axis=1).sort_values(ascending=False).index]

    colors = {"Licensed": "#55a868", "Exempt": "#94a3b8", "Unlicensed": "#C44E52"}
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(share))
    for status in ordered_statuses:
        ax.bar(
            share.index,
            share[status],
            bottom=bottom,
            label=status,
            color=colors.get(status, "#333333"),
        )
        bottom += share[status].values

    ax.set_ylabel("Share of Eligible Listings (%)")
    ax.set_title(
        "Q3 — License Status Among Registration-Eligible Listings",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(title="License Status", loc="upper right")
    fig.tight_layout()
    return fig


def plot_unlicensed_by_borough(
    unlicensed_by_borough: pd.DataFrame,
) -> matplotlib.figure.Figure:
    """Side-by-side bar charts: unlicensed listing count and revenue by borough.
    자치구별 미등록 매물 수 및 매출 나란히 배치 막대 차트.

    Args:
        unlicensed_by_borough: Second element of the tuple returned by
                               `analyze.summarize_revenue_at_risk()`.
                               Required columns: [borough, listing_count,
                               total_revenue, share_of_all_unlicensed_pct].

    Returns:
        matplotlib Figure.
    """
    ub = unlicensed_by_borough.sort_values("listing_count", ascending=True)
    colors = ["#C44E52" if b == "Manhattan" else "#94a3b8" for b in ub["borough"]]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].barh(ub["borough"], ub["listing_count"], color=colors)
    axes[0].set_title("Unlicensed Listing Count by Borough")
    axes[0].set_xlabel("Listing Count")
    for i, v in enumerate(ub["listing_count"]):
        axes[0].text(
            v + 3,
            i,
            f"{v:,} ({ub['share_of_all_unlicensed_pct'].iloc[i]:.0f}%)",
            va="center",
            fontsize=9,
        )

    axes[1].barh(ub["borough"], ub["total_revenue"], color=colors)
    axes[1].set_title("Unlicensed Revenue-at-Risk by Borough")
    axes[1].set_xlabel("Estimated Revenue at Risk ($)")
    axes[1].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"${x/1e6:,.1f}M")
    )

    fig.suptitle("Q3 — Unlicensed Risk Concentration by Borough", fontsize=13)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q4 — Priority Ranking Charts / 우선순위 랭킹 차트
# ---------------------------------------------------------------------------


def plot_pareto_curve(host_rank: pd.DataFrame, gini: float) -> matplotlib.figure.Figure:
    """Pareto/Lorenz-style curve: host rank vs cumulative at-risk revenue share.
    파레토/로렌츠 곡선: 호스트 순위 vs 누적 리스크 매출 비중.

    Args:
        host_rank: Output of `analyze.analyze_host_priority_ranking()`.
        gini: Gini coefficient from `analyze.gini_coefficient()`, shown in the title.

    Returns:
        matplotlib Figure.
    """
    n_50 = int((host_rank["cumulative_pct"] >= 50).idxmax()) + 1
    n_80 = int((host_rank["cumulative_pct"] >= 80).idxmax()) + 1
    total_hosts = len(host_rank)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(
        host_rank["revenue_rank"],
        host_rank["host_revenue"],
        color="#4C72B0",
        alpha=0.7,
        label="Host revenue",
    )
    ax1.set_xlabel("Host rank (sorted by at-risk revenue)")
    ax1.set_ylabel("At-risk Revenue ($)", color="#4C72B0")
    ax1.tick_params(axis="y", labelcolor="#4C72B0")

    ax2 = ax1.twinx()
    ax2.plot(
        host_rank["revenue_rank"],
        host_rank["cumulative_pct"],
        color="#C44E52",
        linewidth=2.2,
    )
    ax2.set_ylabel("Cumulative % of At-risk Revenue", color="#C44E52")
    ax2.tick_params(axis="y", labelcolor="#C44E52")
    ax2.set_ylim(0, 105)

    for target, n, color in [(50, n_50, "#2ca02c"), (80, n_80, "#ff7f0e")]:
        ax2.axhline(target, color=color, linestyle="--", linewidth=1.2)
        ax2.axvline(n, color=color, linestyle="--", linewidth=1.2)
        ax2.scatter([n], [target], color=color, s=70, zorder=5, edgecolor="black")
        ax2.annotate(
            f"{target}% at top {n} hosts",
            xy=(n, target),
            xytext=(8, -12 if target == 80 else 10),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            color=color,
        )

    ax1.set_title(
        f"Q4 — At-risk Revenue Concentration Across {total_hosts} Unlicensed Hosts "
        f"(Gini = {gini:.2f})",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    return fig


def plot_top_priority_hosts(
    host_rank: pd.DataFrame, top_n: int = 15
) -> matplotlib.figure.Figure:
    """Horizontal bar chart of the top-N hosts for compliance outreach.
    컴플라이언스 우선 접촉 대상 상위 N개 호스트 가로 막대그래프.

    Args:
        host_rank: Output of `analyze.analyze_host_priority_ranking()`.
        top_n: Number of top hosts to display.

    Returns:
        matplotlib Figure.
    """
    top = host_rank.head(top_n).sort_values("host_revenue", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(top["host_id"].astype(str), top["host_revenue"], color="#C44E52")
    for bar, listings_n in zip(bars, top["listing_count"]):
        ax.text(
            bar.get_width() * 1.01,
            bar.get_y() + bar.get_height() / 2,
            f"{listings_n} listing(s)",
            va="center",
            fontsize=8,
            color="#333333",
        )

    ax.set_xlabel("At-risk Revenue ($)")
    ax.set_ylabel("Host ID")
    ax.set_title(
        f"Q4 — Top {top_n} Hosts by Unlicensed (At-risk) Revenue",
        fontsize=12,
        fontweight="bold",
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:,.0f}K"))
    fig.tight_layout()
    return fig
