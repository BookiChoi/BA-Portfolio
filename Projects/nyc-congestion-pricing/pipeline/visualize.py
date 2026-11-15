"""Plot functions. Each returns a matplotlib Figure; saving is done by the caller (no plt.show() here).

Why one file: the project has four questions and a shared look; splitting by question would repeat the style code.
"""
import matplotlib

matplotlib.use("Agg")  # why: batch runs on a machine without a display
import matplotlib.pyplot as plt
import numpy as np

SERVICE_LABEL = {"yellow": "Yellow taxi", "fhvhv": "HVFHV (Uber/Lyft)"}
SERVICE_COLOR = {"yellow": "#d4a017", "fhvhv": "#1f4e79"}
AIRPORT_COLOR = "#c0392b"


# ---------------------------------------------------------------- Q1
def plot_q1_top10(top10, dayparts):
    """Ranked horizontal bars: top 10 pickup zones per day-part, per service. Airports highlighted."""
    services = list(top10["service"].unique())
    fig, axes = plt.subplots(len(services), len(dayparts), figsize=(4.2 * len(dayparts), 3.6 * len(services)), squeeze=False)
    for i, s in enumerate(services):
        for j, dp in enumerate(dayparts):
            ax = axes[i, j]
            d = top10[(top10.service == s) & (top10.daypart == dp)].sort_values("rank", ascending=False)
            colors = [AIRPORT_COLOR if a else SERVICE_COLOR[s] for a in d.is_airport]
            ax.barh(d.zone.str.slice(0, 26), d.share * 100, color=colors)
            ax.set_title(f"{SERVICE_LABEL[s]} - {dp}", fontsize=9)
            ax.tick_params(axis="y", labelsize=7)
            ax.set_xlabel("% of valid pickups in the day-part", fontsize=8)
    fig.suptitle("Q1: top 10 pickup zones by day-part, Oct 2025 - Sep 2026 (red = airport zone)", fontsize=11)
    fig.tight_layout()
    return fig


def plot_q1_cumulative(curves, conc):
    """Cumulative share of trips vs zone rank, both services, n50 and n80 marked."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for s, c in curves.items():
        ax.plot(c["rank"], c["cum_share"] * 100, color=SERVICE_COLOR[s], label=SERVICE_LABEL[s], lw=2)
        for key, y in (("n50", 50), ("n80", 80)):
            n = int(conc[s][key])
            ax.plot([n], [y], "o", color=SERVICE_COLOR[s])
            ax.annotate(f"{key}={n}", (n, y), textcoords="offset points", xytext=(6, -12), fontsize=8, color=SERVICE_COLOR[s])
    ax.axhline(50, color="grey", lw=0.6, ls=":")
    ax.axhline(80, color="grey", lw=0.6, ls=":")
    ax.set_xlabel("Zone rank by pickups (1 = busiest)")
    ax.set_ylabel("Cumulative share of valid pickups (%)")
    ax.set_title("Q1: concentration of pickups, Oct 2025 - Sep 2026 (all hours)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_q1_standing(member, service, panels):
    """Zone x month heat table: in (1) or out (0) of the guidance list; one panel per day-part list."""
    n = len(panels)
    sizes = [max(4, member[(member.daypart == p)].zone.nunique()) for p in panels]
    fig, axes = plt.subplots(1, n, figsize=(3.3 * n, 0.26 * max(sizes) + 2.2), squeeze=False)
    for ax, p in zip(axes[0], panels):
        m = member[member.daypart == p]
        piv = m.pivot_table(index="zone", columns="month", values="in_list", aggfunc="max")
        order = piv.sum(axis=1).sort_values(ascending=False).index
        piv = piv.loc[order]
        ax.imshow(piv.values, cmap="Blues", aspect="auto", vmin=0, vmax=1)
        ax.set_yticks(range(len(piv)))
        ax.set_yticklabels([z[:24] for z in piv.index], fontsize=6)
        ax.set_xticks(range(piv.shape[1]))
        ax.set_xticklabels([c[2:] for c in piv.columns], rotation=90, fontsize=6)
        ax.set_title(p, fontsize=9)
    fig.suptitle(f"Q1: {SERVICE_LABEL[service]} - zone in the monthly guidance list (dark = in list)", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- Q2
def plot_q2_destinations(tr):
    """Per service and airport: top 10 destination zones, with the cumulative top-5 share in the title."""
    services = list(tr.service.unique())
    airports = list(tr.airport.unique())
    fig, axes = plt.subplots(len(services), len(airports), figsize=(4.6 * len(airports), 3.8 * len(services)), squeeze=False)
    for i, s in enumerate(services):
        for j, a in enumerate(airports):
            ax = axes[i, j]
            d = tr[(tr.service == s) & (tr.airport == a)].sort_values("rank", ascending=False)
            if d.empty:
                ax.set_axis_off()
                continue
            ax.barh(d.zone.str.slice(0, 26), d.share * 100, color=SERVICE_COLOR[s])
            top5 = d[d["rank"] == 5].cum_share.iloc[0] * 100
            ax.set_title(f"{SERVICE_LABEL[s]} from {a}\ntop-5 share {top5:.1f}%", fontsize=9)
            ax.tick_params(axis="y", labelsize=7)
            ax.set_xlabel("% of valid airport pickups", fontsize=8)
    fig.suptitle("Q2: top 10 destination zones for airport pickups, Oct 2025 - Sep 2026", fontsize=11)
    fig.tight_layout()
    return fig


def plot_q2_dots(res):
    """Dot chart with 95% CI: top-5 share of airport destinations vs top-5 share of all pickups."""
    res = res[res.top5_airport.notna()].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 0.9 * len(res) + 1.5))
    y = np.arange(len(res))[::-1]
    for k, (yi, r) in enumerate(zip(y, res.itertuples())):
        ax.errorbar(r.top5_airport * 100, yi + 0.12,
                    xerr=[[(r.top5_airport - r.top5_airport_lo) * 100], [(r.top5_airport_hi - r.top5_airport) * 100]],
                    fmt="o", color=AIRPORT_COLOR, capsize=3, label="airport destinations" if k == 0 else None)
        ax.errorbar(r.top5_overall * 100, yi - 0.12,
                    xerr=[[(r.top5_overall - r.top5_overall_lo) * 100], [(r.top5_overall_hi - r.top5_overall) * 100]],
                    fmt="s", color=SERVICE_COLOR[r.service], capsize=3, label="all pickups (5 largest pickup zones)" if k == 0 else None)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{SERVICE_LABEL[r.service]}: {r.airport}" for r in res.itertuples()], fontsize=8)
    ax.set_xlabel("Combined share of the 5 largest zones (%), 95% week-block bootstrap CI")
    ax.set_title("Q2: airport destination concentration vs overall pickup concentration")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- Q3
def plot_q3_hourly(hr):
    """Hourly profile by day type: absolute (trips/day) and normalised (share of the day), one column per service."""
    services = list(hr.service.unique())
    fig, axes = plt.subplots(2, len(services), figsize=(6.2 * len(services), 7), squeeze=False)
    colors = {"weekday": "#1f4e79", "weekend": "#c0392b"}
    for j, s in enumerate(services):
        for i, (metric, ylab) in enumerate((("trips_per_day", "Mean trips per day in the hour"), ("share_of_day", "Share of the day's trips"))):
            ax = axes[i, j]
            for typ in ("weekday", "weekend"):
                d = hr[(hr.service == s) & (hr.metric == metric) & (hr.day_type == typ)].sort_values("hour")
                ax.plot(d.hour, d["mean"], color=colors[typ], label=f"{typ} (n={int(d.n_days.iloc[0])} days)")
                ax.fill_between(d.hour, d.lo, d.hi, color=colors[typ], alpha=0.2)
            ax.axvspan(22, 23.99, color="grey", alpha=0.12)
            ax.axvspan(0, 4.99, color="grey", alpha=0.12)
            ax.set_xlabel("Pickup hour (local wall clock); grey = night hours 22-04")
            ax.set_ylabel(ylab)
            ax.set_title(SERVICE_LABEL[s], fontsize=10)
            ax.legend(fontsize=8)
    fig.suptitle("Q3: hourly profile, weekdays (holidays removed) vs weekends, Oct 2025 - Sep 2026 (band = 95% CI across days)", fontsize=10)
    fig.tight_layout()
    return fig


def plot_q3_monthly(dec):
    """Monthly night share by day type, plus gap_m and spread_m (the direct picture of the decision rule)."""
    services = list(dec.service.unique())
    fig, axes = plt.subplots(2, len(services), figsize=(6.2 * len(services), 7), squeeze=False, sharex="col")
    for j, s in enumerate(services):
        d = dec[dec.service == s].sort_values("month")
        x = np.arange(len(d))
        ax = axes[0, j]
        ax.plot(x, d.night_share_weekday * 100, "o-", color="#1f4e79", label="weekday (Mon-Fri, holidays removed)")
        ax.plot(x, d.night_share_weekend * 100, "o-", color="#c0392b", label="weekend (Sat-Sun)")
        ax.set_ylabel("Night share of trips, 22:00-04:59 (%)")
        ax.set_title(SERVICE_LABEL[s], fontsize=10)
        ax.legend(fontsize=8)
        ax = axes[1, j]
        ax.errorbar(x, d.gap_pp, yerr=[d.gap_pp - d.gap_ci_lo_pp, d.gap_ci_hi_pp - d.gap_pp], fmt="o", color="#c0392b", capsize=3,
                    label="gap_m = weekend - weekday (95% CI)")
        ax.plot(x, d.spread_pp, "s--", color="black", label="spread_m (widest Mon-Thu difference)")
        ax.axhline(0, color="grey", lw=0.6)
        ax.set_ylabel("percentage points")
        ax.set_xticks(x)
        ax.set_xticklabels(d.month, rotation=90, fontsize=8)
        ax.legend(fontsize=8)
    fig.suptitle("Q3: night share by day type; decision rule needs gap_m > 0 and gap_m > spread_m in all 12 months", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- Q4
def plot_q4_bars(res):
    """Grouped bars of the Jan-Sep in-zone share per year and service, 95% CI, with the two deltas labelled."""
    services = list(res.service.unique())
    fig, axes = plt.subplots(1, len(services), figsize=(5.6 * len(services), 5), squeeze=False)
    cols = {"2023": "#9ecae1", "2024": "#4292c6", "2026": "#08519c"}
    for ax, s in zip(axes[0], services):
        d = res[(res.service == s) & (res.row_type == "period")].set_index("period")
        for k, p in enumerate(["2023", "2024", "2026"]):
            r = d.loc[p]
            ax.bar(k, r.share * 100, color=cols[p], yerr=[[(r.share - r.share_lo) * 100], [(r.share_hi - r.share) * 100]], capsize=4)
            ax.text(k, r.share * 100 * 0.5, f"{r.share * 100:.1f}%", ha="center", color="white", fontsize=9)
        dl = res[(res.service == s) & (res.row_type == "delta")].set_index("period")
        ax.set_xticks(range(3))
        ax.set_xticklabels(["Jan-Sep 2023", "Jan-Sep 2024", "Jan-Sep 2026"])
        ax.set_ylabel("Trips with a pickup or dropoff in the Congestion Relief Zone list (%)")
        ax.set_title(f"{SERVICE_LABEL[s]}\nDelta_drift (2024-2023) {dl.loc['drift'].share * 100:+.2f} pp;  Delta_main (2026-2024) {dl.loc['main'].share * 100:+.2f} pp", fontsize=9)
    fig.suptitle("Q4: share of trips touching the Congestion Relief Zone list (valid IDs only; error bars = 95% week-block CI)", fontsize=10)
    fig.tight_layout()
    return fig


def plot_q4_monthly(mon):
    """Monthly in-zone share (Jan-Sep) by year, one panel per service."""
    services = list(mon.service.unique())
    fig, axes = plt.subplots(1, len(services), figsize=(5.6 * len(services), 4.5), squeeze=False)
    cols = {2023: "#9ecae1", 2024: "#4292c6", 2026: "#08519c"}
    for ax, s in zip(axes[0], services):
        for y, g in mon[mon.service == s].groupby("year"):
            ax.plot(g.month, g.share * 100, "o-", color=cols[y], label=str(y))
        ax.set_xlabel("Month")
        ax.set_ylabel("In-zone share of valid trips (%)")
        ax.set_title(SERVICE_LABEL[s], fontsize=10)
        ax.legend()
    fig.suptitle("Q4: monthly in-zone share, Jan-Sep by year", fontsize=10)
    fig.tight_layout()
    return fig


def plot_q4_gains(gains):
    """15 largest outside-zone gains in share of pickups and of dropoffs (2024 -> 2026), per service."""
    services = list(gains.service.unique())
    fig, axes = plt.subplots(len(services), 2, figsize=(11, 4.8 * len(services)), squeeze=False)
    for i, s in enumerate(services):
        for j, kind in enumerate(("pickup", "dropoff")):
            ax = axes[i, j]
            d = gains[(gains.service == s) & (gains.kind == kind) & (gains.direction == "gain")].sort_values("delta_pp")
            ax.barh([f"{z[:24]} ({b[:3]})" for z, b in zip(d.zone, d.borough)], d.delta_pp, color=SERVICE_COLOR[s])
            ax.set_title(f"{SERVICE_LABEL[s]}: {kind} share gain", fontsize=9)
            ax.set_xlabel("Change in share of valid trips 2024 -> 2026 (percentage points)", fontsize=8)
            ax.tick_params(axis="y", labelsize=7)
    fig.suptitle("Q4 supplementary: 15 largest gains outside the zone list, Jan-Sep 2024 vs Jan-Sep 2026", fontsize=10)
    fig.tight_layout()
    return fig
