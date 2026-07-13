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
- plt.show()를 절대 호출하지 않는다 — 호출자(caller)가 화면 출력 또는 파일 저장 여부를 결정한다.
- 분석 로직(groupby, 필터, 계산 등)은 analyze.py에 있어야 한다.
"""

from __future__ import annotations

import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


# ---------------------------------------------------------------------------
# Q1 — UK vs Others Donut Chart / UK vs 기타 도넛 차트
# ---------------------------------------------------------------------------

def plot_uk_vs_others(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Donut chart: UK revenue share vs all other countries combined.
    UK 매출 비중 vs 기타 국가 합계 도넛 차트.

    Args:
        df: Output of analyze.analyze_uk_vs_others(). Required columns: [Label, Revenue].
            analyze.analyze_uk_vs_others() 의 출력. 필요 컬럼: [Label, Revenue].

    Returns:
        matplotlib Figure.
    """
    labels  = df["Label"].tolist()
    sizes   = df["Revenue"].tolist()
    colors  = ["#4C72B0", "#DD8452"]
    total   = sum(sizes)

    fig, ax = plt.subplots(figsize=(7, 7))
    _wedges, _texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct=lambda p: f"{p:.1f}%\n(£{p * total / 100:,.0f})",
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5),   # donut shape / 도넛 모양
    )
    for at in autotexts:
        at.set_fontsize(10)

    ax.set_title("Q1 — UK vs Other Countries Revenue Share", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q1 — Country Revenue Bar Chart / 국가별 매출 막대그래프
# ---------------------------------------------------------------------------

def plot_country_revenue(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Horizontal bar chart of revenue by country — all non-UK countries.
    국가별 매출 가로 막대그래프 — 비-UK 전체 국가.

    Args:
        df: Output of analyze.analyze_country_revenue() — all non-UK countries.
            Required columns: [Country, Revenue, RevenueShare_pct].
            analyze.analyze_country_revenue() 의 출력 (전체 비-UK 국가).
            필요 컬럼: [Country, Revenue, RevenueShare_pct].

    Returns:
        matplotlib Figure.
    """
    df = df.sort_values("Revenue", ascending=True)
    n = len(df)
    fig, ax = plt.subplots(figsize=(10, max(5, n * 0.35)))

    bars = ax.barh(df["Country"], df["Revenue"], color="#4C72B0")
    # Revenue share (%) label at each bar end / 각 막대 끝에 매출 비중(%) 라벨 추가
    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(
            bar.get_width() + df["Revenue"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{row['RevenueShare_pct']:.1f}%",
            va="center", fontsize=9, color="#374151",
        )

    ax.set_title("Q1 — Revenue by Country, excl. UK (All Countries)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Total Revenue (£)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q2 — Monthly Revenue Line Chart / 월별 매출 라인 차트
# ---------------------------------------------------------------------------

def plot_monthly_revenue(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Line chart of monthly revenue with Dec-2011 partial-month annotation.
    월별 매출 라인 차트 (2011년 12월 데이터 부분 월 주석 포함).

    Args:
        df: Output of analyze.analyze_monthly_revenue().
            Required columns: [YearMonth (Period), Revenue].
            analyze.analyze_monthly_revenue() 의 출력.
            필요 컬럼: [YearMonth (Period), Revenue].

    Returns:
        matplotlib Figure.
    """
    labels = df["YearMonth"].astype(str).tolist()
    values = df["Revenue"].tolist()

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(labels, values, marker="o", linewidth=2, color="#4C72B0")
    ax.fill_between(labels, values, alpha=0.08, color="#4C72B0")

    # Dec 2011 has only 9 days of data — mark explicitly / 2011년 12월은 9일치 데이터만 있음
    if "2011-12" in labels:
        idx = labels.index("2011-12")
        ax.annotate(
            "⚠ 9 days only",
            xy=(idx, values[idx]),
            xytext=(idx - 1.2, values[idx] * 0.85),
            arrowprops=dict(arrowstyle="->", color="gray"),
            fontsize=9, color="gray",
        )

    ax.set_title("Q2 — Monthly Revenue Trend (Dec 2010 – Dec 2011)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (£)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q2 (continued) — Monthly Revenue Bar Chart / 월별 매출 막대 차트
# ---------------------------------------------------------------------------

def plot_monthly_revenue_bar(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Bar chart of monthly revenue — same data as the line chart, different view.
    월별 매출 막대 차트 — 라인 차트와 동일한 데이터, 다른 시각.

    Bar charts make absolute per-month comparisons easier;
    line charts are better for reading trend direction.
    막대 차트는 각 월의 절대 금액 비교에 유리하고, 라인 차트는 추세 흐름 파악에 유리하다.

    Args:
        df: Output of analyze.analyze_monthly_revenue().
            Required columns: [YearMonth (Period), Revenue].
            analyze.analyze_monthly_revenue() 의 출력.
            필요 컬럼: [YearMonth (Period), Revenue].

    Returns:
        matplotlib Figure.
    """
    labels = df["YearMonth"].astype(str).tolist()
    values = df["Revenue"].tolist()

    fig, ax = plt.subplots(figsize=(13, 5))
    bars = ax.bar(labels, values, color="#4C72B0", edgecolor="white", linewidth=0.4)

    # Highlight Dec 2011 partial month in grey / 2011년 12월 부분 월 강조 (회색)
    if "2011-12" in labels:
        idx = labels.index("2011-12")
        bars[idx].set_color("#d1d5db")
        ax.text(idx, values[idx] * 1.02, "⚠ 9d", ha="center", fontsize=8, color="gray")

    ax.set_title("Q2 — Monthly Revenue (Bar Chart)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (£)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q3 — Product Charts / 상품 차트
# ---------------------------------------------------------------------------

def plot_pareto(pareto_df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Pareto chart validating the 80/20 rule for product revenue.
    상품 매출의 80/20 법칙을 검증하는 파레토 차트.

    Args:
        pareto_df: Output of analyze.analyze_pareto().
                   Required columns: [Description, Revenue, cumulative_pct].
                   analyze.analyze_pareto() 의 출력.
                   필요 컬럼: [Description, Revenue, cumulative_pct].

    Returns:
        matplotlib Figure.
    """
    n_total = len(pareto_df)
    top_20pct_n = int(n_total * 0.20)
    actual_share = pareto_df.iloc[top_20pct_n - 1]["cumulative_pct"]

    # First index where cumulative revenue crosses 80% / 누적 매출이 처음으로 80%를 넘는 지점
    n_for_80 = int((pareto_df["cumulative_pct"] >= 80).values.argmax()) + 1
    pct_products_for_80 = n_for_80 / n_total * 100

    # Plot top ~30% of products so the 20% mark lands near the chart's centre
    # 상위 20% 지점이 차트 중간쯤 오도록 상위 30% 정도만 표시
    n_plot = max(int(n_total * 0.30), int(n_for_80 * 1.2))
    n_plot = min(n_plot, n_total)
    plot_df = pareto_df.head(n_plot)

    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax2 = ax1.twinx()   # right y-axis: cumulative % / 오른쪽 Y축: 누적 비중

    ax1.bar(range(n_plot), plot_df["Revenue"], color="#4C72B0", alpha=0.7)
    ax2.plot(range(n_plot), plot_df["cumulative_pct"], color="#e05c1a", linewidth=2)

    # 80% revenue reference line / 80% 매출 기준선 (가로 빨간 점선)
    ax2.axhline(80, color="#dc2626", linestyle="--", linewidth=1.5, label="80% Revenue")

    # Top-20% product reference line / 상위 20% 상품 기준선 (세로 파란 점선)
    ax1.axvline(top_20pct_n - 1, color="#2563eb", linestyle="--", linewidth=1.5, label="Top 20% Products")

    # Actual cumulative share at the 20% mark / 상위 20% 상품의 실제 누적 매출 비중 마커
    ax2.scatter(top_20pct_n - 1, actual_share, color="#dc2626", s=80, zorder=5)
    ax2.annotate(
        f"Actual share: {actual_share:.1f}%",
        xy=(top_20pct_n - 1, actual_share),
        xytext=(-60, 12), textcoords="offset points",
        fontsize=9, color="#dc2626",
    )

    # Point where 80% revenue is first reached / 80% 매출 달성 지점 마커
    ax2.scatter(n_for_80 - 1, 80, color="#16a34a", s=80, zorder=5)
    ax2.annotate(
        f"80% revenue\nat top {pct_products_for_80:.1f}% products",
        xy=(n_for_80 - 1, 80),
        xytext=(10, -30), textcoords="offset points",
        fontsize=9, color="#16a34a",
    )

    ax1.set_title("Q3 — Pareto Chart: Product Revenue (80/20 Validation)", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Product rank (by revenue)")
    ax1.set_ylabel("Revenue (£)")
    ax2.set_ylabel("Cumulative Revenue %")
    ax2.set_ylim(0, 105)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")

    fig.tight_layout()
    return fig


def plot_top_products(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Horizontal bar chart of top 20 products with frequency rank labels.
    판매 빈도 순위 라벨이 포함된 매출 Top 20 상품 가로 막대그래프.

    Args:
        df: Output of analyze.analyze_product_revenue().
            Required columns: [Description, Revenue, FrequencyRank].
            analyze.analyze_product_revenue() 의 출력.
            필요 컬럼: [Description, Revenue, FrequencyRank].

    Returns:
        matplotlib Figure.
    """
    df = df.sort_values("Revenue", ascending=True)
    fig, ax = plt.subplots(figsize=(12, 9))

    bars = ax.barh(df["Description"], df["Revenue"], color="#4C72B0")
    # Frequency rank label at each bar end / 막대 끝에 판매 빈도 순위 라벨 추가
    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(
            bar.get_width() + df["Revenue"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"Freq Rank: #{int(row['FrequencyRank'])}",
            va="center", fontsize=8, color="gray",
        )

    ax.set_title("Q3 — Top 20 Products by Revenue (with Frequency Rank)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Total Revenue (£)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q3 (continued) — Product Revenue vs Frequency Scatter / 상품 매출 vs 판매량 산점도
# ---------------------------------------------------------------------------

def plot_product_segments(df: pd.DataFrame, top_n: int = 5) -> matplotlib.figure.Figure:
    """Revenue vs Frequency scatter with 4-quadrant segmentation for products.
    상품별 매출 vs 판매 빈도 산점도 (4분면 세그멘테이션).

    Quadrant definitions (median-based split):
        High Rev / High Freq  → Star Product       (효자 상품)
        High Rev / Low Freq   → Niche / Premium    (고가 틈새 상품)
        Low Rev  / High Freq  → Low-price Popular  (단가 낮은 인기 상품)
        Low Rev  / Low Freq   → General            (일반 상품)

    Args:
        df:    Output of analyze.analyze_product_scatter().
               Required columns: [Description, Revenue, Frequency].
               analyze.analyze_product_scatter() 의 출력.
               필요 컬럼: [Description, Revenue, Frequency].
        top_n: Number of top-revenue products to label.
               라벨 표시할 상위 상품 수.

    Returns:
        matplotlib Figure.
    """
    x_med = df["Frequency"].median()
    y_med = df["Revenue"].median()
    top_items = df.nlargest(top_n, "Revenue")

    fig, ax = plt.subplots(figsize=(11, 8))

    ax.scatter(df["Frequency"], df["Revenue"],
               alpha=0.3, s=15, color="#94a3b8", label="All products")
    ax.scatter(top_items["Frequency"], top_items["Revenue"],
               color="#f59e0b", s=60, zorder=5, label=f"Top {top_n} by revenue")

    for _, row in top_items.iterrows():
        ax.annotate(
            row["Description"][:25],
            xy=(row["Frequency"], row["Revenue"]),
            xytext=(6, 4), textcoords="offset points",
            fontsize=7, color="#b45309",
        )

    ax.axvline(x_med, color="navy", linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(y_med, color="navy", linestyle="--", linewidth=1, alpha=0.6)

    rev_max  = df["Revenue"].max()
    freq_max = df["Frequency"].max()

    quadrants = [
        (freq_max * 0.98, rev_max * 0.97,  "right", "top",    "High Rev / High Freq\n(Star Product)",    "#166534", "#dcfce7"),
        (x_med   * 0.02, rev_max * 0.97,  "left",  "top",    "High Rev / Low Freq\n(Niche / Premium)",  "#92400e", "#fef3c7"),
        (freq_max * 0.98, y_med   * 0.05, "right", "bottom", "Low Rev / High Freq\n(Low-price Popular)", "#1e3a5f", "#dbeafe"),
        (x_med   * 0.02, y_med   * 0.05, "left",  "bottom", "Low Rev / Low Freq\n(General)",            "#4b5563", "#f3f4f6"),
    ]
    for x, y, ha, va, label, fc, bg in quadrants:
        ax.text(x, y, label, ha=ha, va=va, fontsize=9, color=fc,
                bbox=dict(boxstyle="round,pad=0.3", fc=bg, alpha=0.7))

    ax.set_title("Q3 — Product Segmentation: Revenue vs Frequency", fontsize=13, fontweight="bold")
    ax.set_xlabel("Frequency (Order Count)")
    ax.set_ylabel("Total Revenue (£)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.88))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q4 — Order Value Distribution / 주문 금액 분포
# ---------------------------------------------------------------------------

def plot_order_value_histogram(order_values: pd.DataFrame) -> matplotlib.figure.Figure:
    """Histogram of order values capped at the 99th percentile.
    99분위수로 cap한 주문 금액 히스토그램.

    Extreme values (top 1%) are excluded from the chart only — the underlying data
    is not modified. This makes the distribution shape visible.
    극단값(상위 1%)은 시각화에서만 제외하며, 원본 데이터는 수정하지 않는다.
    분포 형태를 확인하기 위해 cap을 적용한다.

    Args:
        order_values: Output of analyze.analyze_order_values().
                      Required column: [OrderValue].
                      analyze.analyze_order_values() 의 출력.
                      필요 컬럼: [OrderValue].

    Returns:
        matplotlib Figure.
    """
    p99 = order_values["OrderValue"].quantile(0.99)
    data = order_values[order_values["OrderValue"] <= p99]["OrderValue"]
    median_val = data.median()
    mean_val   = data.mean()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(data, bins=60, color="#4C72B0", edgecolor="white", linewidth=0.4)
    # Median (orange) and mean (red) dashed lines confirm right skew
    # 중앙값(오렌지)과 평균(빨강) 점선으로 우편향 확인
    ax.axvline(median_val, color="orange", linestyle="--", linewidth=1.5, label=f"Median £{median_val:,.0f}")
    ax.axvline(mean_val,   color="red",    linestyle="--", linewidth=1.5, label=f"Mean   £{mean_val:,.0f}")

    ax.set_title(f"Q4 — Order Value Distribution (capped at 99th pct = £{p99:,.0f})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Order Value (£)")
    ax.set_ylabel("Number of Orders")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend()
    fig.tight_layout()
    return fig


def plot_order_value_boxplot(order_values: pd.DataFrame) -> matplotlib.figure.Figure:
    """Box plot of order values capped at the 99th percentile.
    99분위수로 cap한 주문 금액 박스플롯.

    Args:
        order_values: Output of analyze.analyze_order_values().
                      Required column: [OrderValue].
                      analyze.analyze_order_values() 의 출력.
                      필요 컬럼: [OrderValue].

    Returns:
        matplotlib Figure.
    """
    p99 = order_values["OrderValue"].quantile(0.99)
    data = order_values[order_values["OrderValue"] <= p99]["OrderValue"]

    fig, ax = plt.subplots(figsize=(6, 7))
    ax.boxplot(
        data,
        patch_artist=True,
        boxprops=dict(facecolor="#bfdbfe"),                    # box fill / 박스 색
        medianprops=dict(color="orange", linewidth=2),          # median line / 중앙값 선
        flierprops=dict(marker=".", color="gray", alpha=0.3),   # outlier dots / 이상값 점
    )
    ax.set_title(f"Q4 — Order Value Box Plot (capped at 99th pct = £{p99:,.0f})", fontsize=12, fontweight="bold")
    ax.set_ylabel("Order Value (£)")
    ax.set_xticks([])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Q5 — Customer Value Charts / 고객 가치 차트
# ---------------------------------------------------------------------------

def plot_top_customers(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Horizontal bar chart of top 20 customers by revenue with order count labels.
    주문 수 라벨이 포함된 매출 Top 20 고객 가로 막대그래프.

    Args:
        df: Output of analyze.analyze_customer_value().
            Required columns: [CustomerID, TotalRevenue, OrderCount].
            analyze.analyze_customer_value() 의 출력.
            필요 컬럼: [CustomerID, TotalRevenue, OrderCount].

    Returns:
        matplotlib Figure.
    """
    df = df.sort_values("TotalRevenue", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 8))

    bars = ax.barh(
        df["CustomerID"].astype(int).astype(str),
        df["TotalRevenue"],
        color="#4C72B0",
    )
    # Order count label at each bar end / 막대 끝에 주문 횟수 라벨 추가
    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(
            bar.get_width() + df["TotalRevenue"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['OrderCount'])} orders",
            va="center", fontsize=8, color="gray",
        )

    ax.set_title("Q5 — Top 20 Customers by Revenue (with Order Count)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Total Revenue (£)")
    ax.set_ylabel("CustomerID")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    fig.tight_layout()
    return fig


def plot_customer_revenue_histogram(cust_profile: pd.DataFrame) -> matplotlib.figure.Figure:
    """Histogram of total revenue per customer, capped at 99th percentile.
    고객별 총매출 분포 히스토그램 (99분위수 cap).

    Confirms right-skew in the customer revenue distribution;
    visualises the gap between median and mean.
    고객 매출 분포의 우편향 정도를 확인하고 중앙값/평균 차이를 시각화한다.

    Args:
        cust_profile: DataFrame with columns [CustomerID, TotalRevenue, OrderCount].
                      [CustomerID, TotalRevenue, OrderCount] 컬럼의 DataFrame.

    Returns:
        matplotlib Figure.
    """
    p99 = cust_profile["TotalRevenue"].quantile(0.99)
    data = cust_profile[cust_profile["TotalRevenue"] <= p99]["TotalRevenue"]
    median_val = data.median()
    mean_val   = data.mean()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(data, bins=60, color="#7c3aed", edgecolor="white", linewidth=0.4)
    ax.axvline(median_val, color="orange", linestyle="--", linewidth=1.5,
               label=f"Median £{median_val:,.0f}")
    ax.axvline(mean_val,   color="red",    linestyle="--", linewidth=1.5,
               label=f"Mean   £{mean_val:,.0f}")

    ax.set_title(f"Q5 — Customer Revenue Distribution (capped at 99th pct = £{p99:,.0f})",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Total Revenue per Customer (£)")
    ax.set_ylabel("Number of Customers")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend()
    fig.tight_layout()
    return fig


def plot_vip_seasonal(
    cust_df: pd.DataFrame,
    vip_ids: "pd.Index | list",
) -> matplotlib.figure.Figure:
    """Normalised monthly revenue comparison: VIP vs Non-VIP customers.
    VIP vs 일반 고객 월별 매출 추이 비교 (정규화).

    Normalisation (0–100) removes the absolute revenue difference so seasonal
    patterns can be compared fairly between the two groups.
    정규화(0~100)를 적용해 절대 금액 차이에 관계없이 계절성 패턴을 비교한다.

    Key finding from EDA:
        VIP customers peak in November (bulk pre-purchase).
        Non-VIP customers peak in December (last-minute Christmas purchase).
    EDA 주요 발견:
        VIP는 11월 피크 (사전 대량 구매). Non-VIP는 12월 피크 (막판 크리스마스 구매).

    Args:
        cust_df: CustomerID-filtered DataFrame from clean.get_customer_df().
                 Required columns: [InvoiceDate, Revenue, CustomerID].
                 clean.get_customer_df() 출력. 필요 컬럼: [InvoiceDate, Revenue, CustomerID].
        vip_ids: Array of VIP CustomerIDs from analyze.get_vip_ids().
                 analyze.get_vip_ids() 의 VIP CustomerID 배열.

    Returns:
        matplotlib Figure.
    """
    vip_df     = cust_df[cust_df["CustomerID"].isin(vip_ids)].copy()
    non_vip_df = cust_df[~cust_df["CustomerID"].isin(vip_ids)].copy()

    for frame in (vip_df, non_vip_df):
        frame["YearMonth"] = frame["InvoiceDate"].dt.to_period("M")

    vip_monthly     = vip_df.groupby("YearMonth")["Revenue"].sum()
    non_vip_monthly = non_vip_df.groupby("YearMonth")["Revenue"].sum()

    def _normalise(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng * 100 if rng > 0 else s * 0

    vip_norm     = _normalise(vip_monthly)
    non_vip_norm = _normalise(non_vip_monthly)

    months       = sorted(set(vip_monthly.index) | set(non_vip_monthly.index))
    month_labels = [str(m) for m in months]

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(month_labels, [vip_norm.get(m, None) for m in months],
            marker="s", linewidth=2, color="#dc2626",
            label=f"VIP (n={len(vip_ids):,})")
    ax.plot(month_labels, [non_vip_norm.get(m, None) for m in months],
            marker="o", linewidth=2, color="#3b82f6",
            label="Non-VIP")

    ax.set_title("Q5 — Monthly Revenue: VIP vs Non-VIP (normalised 0–100)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Normalised Revenue (0 = min, 100 = max)")
    ax.set_xticks(range(len(month_labels)))
    ax.set_xticklabels(month_labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def plot_customer_segments(cust_profile: pd.DataFrame, top_n: int = 10) -> matplotlib.figure.Figure:
    """Revenue vs Frequency scatter plot with 4-quadrant customer segmentation.
    매출 vs 구매 빈도 산점도 (4분면 고객 세그멘테이션).

    Quadrant definitions (median-based split):
        High Rev / High Freq  → VIP               (VIP 고객)
        High Rev / Low Freq   → Big Spender        (고액 단발 구매자, B2B?)
        Low Rev  / High Freq  → Loyal Small Buyer  (단골 소액 구매자)
        Low Rev  / Low Freq   → Casual             (일반 고객)

    Args:
        cust_profile: DataFrame with columns [CustomerID, TotalRevenue, OrderCount].
                      [CustomerID, TotalRevenue, OrderCount] 컬럼의 DataFrame.
        top_n:        Number of top-revenue customers to highlight.
                      강조 표시할 상위 고객 수.

    Returns:
        matplotlib Figure.
    """
    x_med = cust_profile["OrderCount"].median()
    y_med = cust_profile["TotalRevenue"].median()
    top10 = cust_profile.nlargest(top_n, "TotalRevenue")

    fig, ax = plt.subplots(figsize=(11, 8))

    # All customers (grey, translucent) / 전체 고객 산점도 (회색, 반투명)
    ax.scatter(cust_profile["OrderCount"], cust_profile["TotalRevenue"],
               alpha=0.3, s=15, color="#94a3b8", label="All customers")
    # Top-N customers highlighted in red / 상위 N 고객 강조 (빨간색)
    ax.scatter(top10["OrderCount"], top10["TotalRevenue"],
               color="#ef4444", s=60, zorder=5, label=f"Top {top_n} by revenue")

    for _, row in top10.iterrows():
        ax.annotate(
            f"ID {int(row['CustomerID'])}",
            xy=(row["OrderCount"], row["TotalRevenue"]),
            xytext=(6, 4), textcoords="offset points",
            fontsize=7, color="#ef4444",
        )

    # Quadrant dividers (median-based) / 4분면 기준선 (중앙값 기준)
    ax.axvline(x_med, color="navy", linestyle="--", linewidth=1, alpha=0.6)
    ax.axhline(y_med, color="navy", linestyle="--", linewidth=1, alpha=0.6)

    rev_max  = cust_profile["TotalRevenue"].max()
    freq_max = cust_profile["OrderCount"].max()

    quadrants = [
        (freq_max * 0.98, rev_max * 0.97,  "right", "top",    "High Rev / High Freq\n(VIP)",             "#166534", "#dcfce7"),
        (x_med   * 0.02, rev_max * 0.97,  "left",  "top",    "High Rev / Low Freq\n(Big Spender)",       "#92400e", "#fef3c7"),
        (freq_max * 0.98, y_med   * 0.05, "right", "bottom", "Low Rev / High Freq\n(Loyal Small Buyer)", "#1e3a5f", "#dbeafe"),
        (x_med   * 0.02, y_med   * 0.05, "left",  "bottom", "Low Rev / Low Freq\n(Casual)",             "#4b5563", "#f3f4f6"),
    ]
    for x, y, ha, va, label, fc, bg in quadrants:
        ax.text(x, y, label, ha=ha, va=va, fontsize=9, color=fc,
                bbox=dict(boxstyle="round,pad=0.3", fc=bg, alpha=0.7))

    ax.set_title("Q5 — Customer Segmentation: Revenue vs Purchase Frequency", fontsize=13, fontweight="bold")
    ax.set_xlabel("Order Count (Frequency)")
    ax.set_ylabel("Total Revenue (£)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.88))
    fig.tight_layout()
    return fig
