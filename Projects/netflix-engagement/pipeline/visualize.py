"""Figures for Q1. Every function takes an aggregated DataFrame (the same one saved as CSV next to
the PNG) and returns a matplotlib Figure. No plt.show() here; main.py saves the figures."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _halves(df):
    return list(dict.fromkeys(df["half"]))


def plot_share_lines(shares: pd.DataFrame) -> plt.Figure:
    """Check 1 shares per half-year; H2 columns shaded so alternation is visible by eye."""
    fig, ax = plt.subplots(figsize=(9, 5))
    hs = _halves(shares)
    for i, h in enumerate(hs):
        if h.startswith("H2"):
            ax.axvspan(i - 0.5, i + 0.5, color="grey", alpha=0.12, lw=0)
    for g, d in shares.groupby("genre", sort=False):
        ax.plot(range(len(hs)), d["share_pct"].to_numpy(), marker="o", label=g)
    ax.set_xticks(range(len(hs)), hs)
    ax.set_ylabel("share of labelled hours (%)")
    ax.set_title("Genre share by half-year, eligible genres (check 1, all labelled titles)\nshaded = H2")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


def plot_shift_bars(shifts: pd.DataFrame, theta: float) -> plt.Figure:
    """Six shifts per genre; transitions H1->H2 and H2->H1 coloured differently; +/-theta band."""
    gs = list(dict.fromkeys(shifts["genre"]))
    ncol = 3
    nrow = int(np.ceil(len(gs) / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(12, 3 * nrow), squeeze=False, sharey=True)
    for ax, g in zip(axs.ravel(), gs):
        d = shifts[shifts["genre"] == g]
        cols = ["tab:blue" if t.startswith("H1") else "tab:orange" for t in d["transition"]]
        ax.bar(range(len(d)), d["shift_pp"], color=cols, yerr=[d["shift_pp"] - d["ci_lo"], d["ci_hi"] - d["shift_pp"]],
               capsize=2)
        ax.axhspan(-theta, theta, color="red", alpha=0.08)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xticks(range(len(d)), [t.replace(" -> ", "\n") for t in d["transition"]], fontsize=6)
        ax.set_title(g, fontsize=9)
    for ax in axs.ravel()[len(gs):]:
        ax.axis("off")
    fig.suptitle(f"Half-year shifts in pp (blue H1->H2, orange H2->H1), band = +/-{theta} pp, bars = 95% bootstrap CI")
    fig.tight_layout()
    return fig


def plot_check_matrix(cm: pd.DataFrame, theta: float) -> plt.Figure:
    """Genre x check margin in the genre's best direction, annotated with CI; green = margin >= theta."""
    gs = list(dict.fromkeys(cm["genre"]))
    checks = list(dict.fromkeys(cm["check"]))
    M = np.full((len(gs), len(checks)), np.nan)
    fig, ax = plt.subplots(figsize=(9, 0.6 * len(gs) + 2))
    for _, r in cm.iterrows():
        M[gs.index(r["genre"]), checks.index(r["check"])] = r["margin_pp"]
    im = ax.imshow(M, cmap="RdYlGn", vmin=-theta * 2, vmax=theta * 2, aspect="auto")
    for _, r in cm.iterrows():
        i, j = gs.index(r["genre"]), checks.index(r["check"])
        ax.text(j, i, f"{r['margin_pp']:.2f}\n[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]", ha="center", va="center", fontsize=7,
                fontweight="bold" if r["margin_pp"] >= theta else "normal")
    ax.set_xticks(range(len(checks)), checks)
    ax.set_yticks(range(len(gs)), [f"{g} ({d})" for g, d in zip(gs, cm.drop_duplicates('genre')['direction'])])
    ax.set_title(f"Margin in pp (bold = pass at {theta} pp), [95% bootstrap CI]")
    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    return fig


def plot_perm_null(Ms: np.ndarray, observed: float, theta: float, title: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(Ms, bins=40, color="grey")
    ax.axvline(observed, color="red", label=f"observed M = {observed:.2f}")
    ax.axvline(theta, color="blue", ls="--", label=f"pass threshold {theta} pp")
    q = np.quantile(Ms, 0.95)
    ax.axvline(q, color="green", ls=":", label=f"95th percentile of null = {q:.2f}")
    ax.set_xlabel("M = max over eligible genres of the genre margin (pp)")
    ax.set_ylabel("number of orderings")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_coverage(cov: pd.DataFrame, match: pd.DataFrame) -> plt.Figure:
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axs[0]
    x = np.arange(len(cov))
    ax.bar(x, cov["labelled_over_inscope_pct"], color="tab:green")
    ax.axhline(90, color="red", ls="--", lw=1, label="90% (coverage rule)")
    ax.set_xticks(x, cov["half"], rotation=30)
    ax.set_ylabel("labelled hours / in-scope hours (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.set_title("Labelled-hours coverage")
    ax = axs[1]
    ax.errorbar(range(len(match)), match["rate_pct"], yerr=[match["rate_pct"] - match["ci_lo_pct"], match["ci_hi_pct"] - match["rate_pct"]],
                fmt="o", capsize=4)
    ax.set_xticks(range(len(match)), match["group"])
    ax.set_ylabel("matched keys (%) with 95% Wilson CI")
    ax.set_title("Match rate, tagged vs untagged")
    fig.tight_layout()
    return fig
