"""Q1 analysis: genre shares, shifts, margins, three checks, bootstrap, permutation, Newcombe CI.

Everything here is a pure function on arrays so it can be unit-tested on synthetic data.
Conventions (plan, Q1 section): positions t = 0..6 are H1 2023 ... H1 2026. Shift d_i = s[i+1]-s[i].
Direction "up" means the genre peaks in H2: shifts at even index (H1->H2) are positive and shifts at
odd index (H2->H1) are negative. Direction "down" flips all signs.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pandas as pd

TOL = 1e-9  # plan: tolerance for the pass test
NEAR = 0.05  # plan: near misses within 0.05 pp are listed
SIGN_UP = np.array([1, -1, 1, -1, 1, -1], dtype=float)  # signs of the six shifts for "up"
CHECKS = ("c1", "c2", "c3n", "c3c")


# --------------------------------------------------------------------------- shares
def group_shares(H, G, weights=None, mask=None):
    """Genre share in percent, shape (n_groups, T).

    H: keys x T hours; G: keys x n_groups one-hot; weights: per key (bootstrap counts) or keys x T
    (post-stratification); mask: keys x T bool of the cells that take part (check variants).
    The denominator is the sum over the labelled cells that take part, so shares sum to 100 per
    column (NaN if a column is empty).
    """
    X = H.astype(float)
    if mask is not None:
        X = X * mask
    if weights is not None:
        X = X * (weights if weights.ndim == 2 else weights[:, None])
    num = G.T @ X
    den = num.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return 100.0 * num / den


def shifts(S):
    """d_i = S[:, i+1] - S[:, i]."""
    return S[:, 1:] - S[:, :-1]


def margins(D, start=0):
    """Directional margins (up, down) per genre: min over the aligned shifts, in pp.

    ``start`` is the index of the first transition inside the six-transition pattern
    (0 for checks 1 and 2, 1 for check 3 which uses d2..d6).
    """
    sg = SIGN_UP[start:start + D.shape[1]]
    return np.min(D * sg, axis=1), np.min(-D * sg, axis=1)


@dataclass
class Variants:
    """Shares (G x 7) for the four variants that enter the pass rule."""
    c1: np.ndarray   # all labelled titles
    c2: np.ndarray   # top-10 keys per half dropped
    c3n: np.ndarray  # "new" stratum (column 0 NaN)
    c3c: np.ndarray  # "carried over" stratum (column 0 NaN)


def variant_shares(H, G, top10, new, carried, weights=None):
    return Variants(group_shares(H, G, weights), group_shares(H, G, weights, mask=~top10),
                    group_shares(H, G, weights, mask=new), group_shares(H, G, weights, mask=carried))


def variant_margins(v):
    """dict check -> array (G, 2) with columns (up, down)."""
    out = {}
    for name in CHECKS:
        S = getattr(v, name)
        if name in ("c3n", "c3c"):
            up, down = margins(shifts(S[:, 1:]), start=1)
        else:
            up, down = margins(shifts(S), start=0)
        out[name] = np.column_stack([up, down])
    return out


def genre_margin(m, names=CHECKS):
    """Genre margin = max over direction of the min over the checks. Returns (margin, direction 0=up/1=down).

    A NaN anywhere (empty stratum) must never pass, so it is mapped to -inf.
    """
    stack = np.stack([m[n] for n in names], axis=0)  # checks x G x 2
    per_dir = np.where(np.isnan(stack).any(axis=0), -np.inf, np.min(stack, axis=0))
    return per_dir.max(axis=1), per_dir.argmax(axis=1)


# --------------------------------------------------------------------------- bootstrap
def cluster_bootstrap(H, G, top10, new, carried, eligible, direction, n_boot=2000, seed=42):
    """Resample title keys with replacement, jointly across all halves.

    Why multinomial counts: resampling n keys with replacement equals a vector of counts, so each key
    keeps its seven half-year hours together (cluster = key). Top-10 sets and new/carried flags stay at
    their observed per-key values (plan). Only labelled keys are resampled, so the result is
    conditional on the labelling. ``direction`` (E,) is the observed direction (0 up, 1 down) used to
    sign the aligned shifts and per-check margins of the eligible genres.
    """
    rng = np.random.default_rng(seed)
    n = H.shape[0]
    E = len(eligible)
    sg = np.where(direction == 0, 1.0, -1.0)[:, None] * SIGN_UP[None, :]
    out = {"shift": np.empty((n_boot, E, 6)), "mean_aligned": np.empty((n_boot, E)),
           "check_margin": np.empty((n_boot, E, 4)), "gmargin": np.empty((n_boot, E)),
           "gmargin_any": np.empty((n_boot, E)), "gdir": np.empty((n_boot, E), dtype=int),
           "share": np.empty((n_boot, E, H.shape[1]))}
    for r in range(n_boot):
        w = rng.multinomial(n, np.full(n, 1.0 / n)).astype(float)
        v = variant_shares(H, G, top10, new, carried, weights=w)
        m = variant_margins(v)
        D = shifts(v.c1)[eligible]
        out["shift"][r] = D
        out["share"][r] = v.c1[eligible]
        out["mean_aligned"][r] = (D * sg).mean(axis=1)
        for j, nm in enumerate(CHECKS):
            out["check_margin"][r, :, j] = m[nm][eligible, direction]
        g, gd = genre_margin(m)
        out["gmargin"][r] = g[eligible]
        out["gdir"][r] = gd[eligible]
    return out


def pct_ci(x, axis=0, level=0.95):
    a = (1 - level) / 2
    return np.nanpercentile(x, 100 * a, axis=axis), np.nanpercentile(x, 100 * (1 - a), axis=axis)


# --------------------------------------------------------------------------- permutation
def permutation_test(v, eligible, thetas=(1.5, 2.0, 3.0), fix_first=False):
    """Exact enumeration of half-year orderings; statistic M = max over eligible genres of the genre margin.

    fix_first=False: check 1 only, all 7! orderings. fix_first=True: all four variants with H1 2023 kept
    at position 0 (6! orderings) because check 3 strata do not exist for H1 2023. The identity ordering
    is included in the enumeration, so p >= 1/n_orderings.
    """
    T = v.c1.shape[1]
    names = CHECKS if fix_first else ("c1",)
    perms = itertools.permutations(range(1, T)) if fix_first else itertools.permutations(range(T))
    Ms = []
    for p in perms:
        idx = np.array((0,) + p) if fix_first else np.array(p)
        vv = Variants(v.c1[:, idx], v.c2[:, idx], v.c3n[:, idx], v.c3c[:, idx])
        g, _ = genre_margin(variant_margins(vv), names=names)
        Ms.append(g[eligible].max())
    Ms = np.array(Ms)
    gm, _ = genre_margin(variant_margins(v), names=names)
    obs = float(gm[eligible].max())
    out = {"n_orderings": int(len(Ms)), "observed_M": obs, "p_value": float(np.mean(Ms >= obs - TOL)),
           "any_pass_fraction": {str(t): float(np.mean(Ms >= t - TOL)) for t in thetas},
           "any_pass_count": {str(t): int(np.sum(Ms >= t - TOL)) for t in thetas}}
    return out, Ms


# --------------------------------------------------------------------------- pair rule
def pair_rule(shift_mat, names, r_cut=-0.9):
    """Connected groups of passing genres whose six check-1 shifts correlate with r <= r_cut."""
    k = len(names)
    parent = list(range(k))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    pairs = []
    for i, j in itertools.combinations(range(k), 2):
        r = float(np.corrcoef(shift_mat[i], shift_mat[j])[0, 1])
        pairs.append({"a": names[i], "b": names[j], "r": r})
        if r <= r_cut:
            parent[find(i)] = find(j)
    comps = {}
    for i in range(k):
        comps.setdefault(find(i), []).append(names[i])
    return list(comps.values()), pairs


# --------------------------------------------------------------------------- Newcombe CI
def _wilson(x, n, z=1.959964):
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def newcombe_diff(x1, n1, x2, n2):
    """Newcombe hybrid-score 95% CI for p1 - p2 (method 10). Returns (diff, lo, hi)."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = _wilson(x1, n1)
    l2, u2 = _wilson(x2, n2)
    d = p1 - p2
    return d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


# --------------------------------------------------------------------------- matrices
def build_matrices(half_keys: pd.DataFrame, halves: list[str], union_kids: list[str]):
    """Key x half hour matrix for the scope union plus top-10, new and carried-over masks.

    - top10: the 10 keys with most hours per half among ALL listed keys (labelled or not, plan check 2);
      ties broken by key id so the set is deterministic.
    - new / carried (check 3): key absent / present in the previous half's cleaned file. For H2 2023 the
      comparison with H1 2023 uses the cleaned title only (amendment 1), because H1 2023 types are partly
      inferred; for later halves the typed key id is used.
    """
    T = len(halves)
    pv = half_keys.pivot_table(index="kid", columns="half", values="hours", aggfunc="sum")[halves]
    H = pv.reindex(union_kids).fillna(0.0).to_numpy()
    top10 = np.zeros_like(H, dtype=bool)
    pos = {k: i for i, k in enumerate(union_kids)}
    for t, h in enumerate(halves):
        g = half_keys[half_keys["half"] == h].sort_values(["hours", "kid"], ascending=[False, True]).head(10)
        for k in g["kid"]:
            if k in pos:
                top10[pos[k], t] = True
        assert g["kid"].isin(pos).all(), "top-10 key outside the scope union (scope rule violated)"
    key_of = half_keys.drop_duplicates("kid").set_index("kid")["key"]
    h1_titles = set(half_keys.loc[half_keys["half"] == halves[0], "key"])
    present = H > 0
    new = np.zeros_like(present)
    carried = np.zeros_like(present)
    for t in range(1, T):
        if t == 1:
            prev = np.array([key_of[k] in h1_titles for k in union_kids])
        else:
            prev = present[:, t - 1]
        new[:, t] = present[:, t] & ~prev
        carried[:, t] = present[:, t] & prev
    return H, top10, new, carried
