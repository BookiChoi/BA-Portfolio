"""Shared analysis helpers: cache loading, week-block bootstrap, concentration stats, Holm correction.

Why week blocks: trips within a day and days within a week are strongly dependent, so resampling whole
Mon-Sun weeks gives honest CIs (plan section 0). Weights are drawn once per call so that two quantities
resampled "jointly" (e.g. airport share and overall share) use the same weeks.
"""
import numpy as np
import pandas as pd

from . import config as C, load as L


def load_cache(service, kind, months):
    frames = []
    for ym in months:
        frames.append(pd.read_parquet(C.CACHE / f"{service}_{ym[0]}-{ym[1]:02d}_{kind}.parquet"))
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    return d


def week_start(dates: pd.Series) -> pd.Series:
    """Monday of the calendar week (Mon-Sun blocks, plan section 0)."""
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def valid_zone_ids():
    lk = L.read_lookup()
    return sorted(set(lk.LocationID) - set(L.invalid_zone_ids(lk)))


def boot_weights(n_weeks: int, B: int, rng: np.random.Generator) -> np.ndarray:
    """B x n_weeks matrix; entry = how often a week is drawn in a replicate (resampling weeks with replacement)."""
    idx = rng.integers(0, n_weeks, size=(B, n_weeks))
    W = np.zeros((B, n_weeks))
    for b in range(B):
        W[b] = np.bincount(idx[b], minlength=n_weeks)
    return W


def pct_ci(x, lo=2.5, hi=97.5):
    return float(np.percentile(x, lo)), float(np.percentile(x, hi))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (step-down, monotone)."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def one_sided_boot_p(stat_reps, direction="greater"):
    """Bootstrap p for H1: stat > 0 (or < 0). (1 + #{replicates on the wrong side or at 0}) / (B + 1).

    Why +1: avoids reporting p = 0 with a finite number of replicates.
    """
    x = np.asarray(stat_reps)
    wrong = (x <= 0).sum() if direction == "greater" else (x >= 0).sum()
    return float((1 + wrong) / (len(x) + 1))


def concentration(R: np.ndarray) -> dict:
    """R: (k, Z) count rows. Returns n50, n80, top5 share and active share for each row."""
    R = np.atleast_2d(R).astype(float)
    tot = R.sum(axis=1, keepdims=True)
    S = -np.sort(-R, axis=1)
    cum = np.cumsum(S, axis=1) / tot
    return {"n50": (cum < 0.5).sum(axis=1) + 1, "n80": (cum < 0.8).sum(axis=1) + 1,
            "top5": cum[:, 4], "active": (R > 0).mean(axis=1)}


def ranked(counts: np.ndarray, ids: np.ndarray):
    """Ranking by count desc, ties by zone ID ascending (plan Q1)."""
    order = np.lexsort((ids, -counts))
    return ids[order], counts[order]


def cover_list(counts: np.ndarray, ids: np.ndarray, frac: float):
    """Smallest set of zones whose cumulative trip share reaches frac (ties by ID)."""
    rid, rc = ranked(counts, ids)
    cum = np.cumsum(rc) / rc.sum()
    k = int((cum < frac).sum() + 1)
    return list(rid[:k])
