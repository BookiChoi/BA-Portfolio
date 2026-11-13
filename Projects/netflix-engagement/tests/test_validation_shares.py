"""Validator: independent recomputation of margins, passes, eligibility, permutation tests and Newcombe CIs
from the analyst's aggregated share table (outputs/q1/shares_all_variants.csv). Own implementation, pure
python loops on dicts; does not import pipeline.analyze.

Run: pytest -q -s tests/test_validation_shares.py
"""
import itertools
import json
import math
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / "outputs" / "q1"
HALVES = ["H1 2023", "H2 2023", "H1 2024", "H2 2024", "H1 2025", "H2 2025", "H1 2026"]
VARS = ["c1", "c2", "c3n", "c3c"]


@pytest.fixture(scope="module")
def sh():
    df = pd.read_csv(Q / "shares_all_variants.csv")
    out = {}
    for (v, g), d in df.groupby(["variant", "genre"]):
        s = dict(zip(d["half"], d["share_pct"]))
        out[(v, g)] = [s[h] for h in HALVES]
    return df, out


def aligned_margin(series, first_pos, direction):
    """series: shares at consecutive positions starting at calendar position first_pos (0 = H1 2023).
    A transition from position p to p+1 is H1->H2 when p is even. Direction +1 ("up"): H1->H2 rises, H2->H1 falls."""
    vals = []
    for k in range(len(series) - 1):
        p = first_pos + k
        d = series[k + 1] - series[k]
        vals.append(direction * d if p % 2 == 0 else -direction * d)
    return min(vals)


def margins_for(sh_map, g, perm=None):
    res = {}
    for dirn in (+1, -1):
        row = {}
        for v in VARS:
            s = sh_map[(v, g)]
            if perm is not None:
                s = [s[i] for i in perm]
            if v in ("c3n", "c3c"):
                if any(math.isnan(x) for x in s[1:]):
                    row[v] = -math.inf
                    continue
                row[v] = aligned_margin(s[1:], 1, dirn)
            else:
                row[v] = aligned_margin(s, 0, dirn)
        res[dirn] = row
    return res


def test_shares_sum_to_100(sh):
    df, _ = sh
    g = df.dropna(subset=["share_pct"]).groupby(["variant", "half"])["share_pct"].sum()
    print("SUM-OF-SHARES min/max", g.min(), g.max(), "n cells", len(g))
    assert (g - 100).abs().max() < 1e-6
    nan = df[df.share_pct.isna()]
    assert set(nan.variant) <= {"c3n", "c3c"} and set(nan.half) == {"H1 2023"}


def test_margins_and_eligibility(sh):
    df, S = sh
    gr = pd.read_csv(Q / "genre_results.csv")
    all_genres = sorted({g for (_, g) in S})
    mean_share = {g: sum(S[("c1", g)]) / 7 for g in all_genres}
    elig = sorted([g for g in all_genres if mean_share[g] >= 5.0])
    print("ELIGIBLE (mine)", elig)
    print("MEAN SHARES (mine)", {g: round(v, 2) for g, v in mean_share.items()})
    assert elig == sorted(gr.genre)
    worst = 0
    for _, r in gr.iterrows():
        g = r.genre
        assert abs(mean_share[g] - r.mean_share_pct) < 1e-6
        m = margins_for(S, g)
        best = {d: min(m[d].values()) for d in m}
        dirn = +1 if best[+1] >= best[-1] else -1
        gm = best[dirn]
        mine_dir = "up" if dirn == 1 else "down"
        row = [m[dirn][v] for v in VARS]
        want = [r.margin_c1, r.margin_c2, r.margin_c3n, r.margin_c3c]
        diffs = [abs(a - b) for a, b in zip(row, want)] + [abs(gm - r.genre_margin_pp)]
        s = S[("c1", g)]
        sh_mine = [s[i + 1] - s[i] for i in range(6)]
        diffs += [abs(sh_mine[i] - r[f"shift_{i + 1}"]) for i in range(6)]
        al = [(dirn if i % 2 == 0 else -dirn) * sh_mine[i] for i in range(6)]
        diffs.append(abs(sum(al) / 6 - r.mean_aligned_shift_pp))
        for nm in ("c3n", "c3c"):
            ss = S[(nm, g)][1:]
            a5 = [(dirn if (i + 1) % 2 == 0 else -dirn) * (ss[i + 1] - ss[i]) for i in range(5)]
            diffs.append(abs(sum(a5) / 5 - r[f"mean_aligned_shift_{nm}_5trans"]))
        mx = max(diffs)
        worst = max(worst, mx)
        p2 = bool(r["pass_theta_2.0"])
        print(f"GENRE {g}: dir mine={mine_dir} analyst={r.direction}; margins mine={[round(x, 4) for x in row]} "
              f"gm mine={gm:.4f} analyst={r.genre_margin_pp:.4f}; max abs diff over 17 numbers={mx:.2e}; "
              f"pass2 mine={gm >= 2 - 1e-9} analyst={p2}")
        assert mine_dir == r.direction
        assert mx < 1e-6
    print("WORST DIFF", worst)


def test_pass_counts_all_thetas(sh):
    _, S = sh
    gr = pd.read_csv(Q / "genre_results.csv")
    for th in (1.5, 2.0, 3.0):
        n_mine = 0
        for g in gr.genre:
            m = margins_for(S, g)
            gm = max(min(m[d].values()) for d in m)
            n_mine += gm >= th - 1e-9
        n_an = int(gr[f"pass_theta_{th}"].sum())
        print(f"PASSING GENRES theta={th}: mine={n_mine} analyst={n_an}")
        assert n_mine == n_an == 0


def perm_stats(S, genres, fix_first):
    Ms = []
    it = itertools.permutations(range(1, 7)) if fix_first else itertools.permutations(range(7))
    for p in it:
        perm = [0] + list(p) if fix_first else list(p)
        best = -math.inf
        for g in genres:
            m = margins_for(S, g, perm)
            gm = max(min(m[d].values()) for d in m) if fix_first else max(m[d]["c1"] for d in m)
            best = max(best, gm)
        Ms.append(best)
    return Ms


def test_permutation_tests(sh):
    _, S = sh
    res = json.loads((Q / "results.json").read_text())
    gr = pd.read_csv(Q / "genre_results.csv")
    genres = list(gr.genre)
    for name, fix_first, key in (("check1", False, "permutation_check1_only"), ("all", True, "permutation_all_checks")):
        Ms = perm_stats(S, genres, fix_first)
        if fix_first:
            obs = max(max(min(margins_for(S, g)[d].values()) for d in (1, -1)) for g in genres)
        else:
            obs = max(max(margins_for(S, g)[d]["c1"] for d in (1, -1)) for g in genres)
        p = sum(1 for x in Ms if x >= obs - 1e-9) / len(Ms)
        a = res[key]
        anypass = {t: sum(1 for x in Ms if x >= t - 1e-9) for t in (1.5, 2.0, 3.0)}
        print(f"PERM {name}: n mine={len(Ms)} analyst={a['n_orderings']}; observed M mine={obs:.4f} analyst={a['observed_M']:.4f}; "
              f"p mine={p:.4f} analyst={a['p_value']:.4f}; any-pass counts mine={anypass} analyst={a['any_pass_count']}")
        assert len(Ms) == a["n_orderings"]
        assert abs(obs - a["observed_M"]) < 1e-6
        assert abs(p - a["p_value"]) < 1e-9
        for t in (1.5, 2.0, 3.0):
            assert anypass[t] == a["any_pass_count"][str(t)]


def wilson(x, n, z=1.959963984540054):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def newcombe(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p1 - p2
    return d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def test_newcombe_and_match_rates():
    mr = pd.read_csv(Q / "match_rate.csv")
    res = json.loads((Q / "results.json").read_text())
    for outcome in ("matched", "labelled"):
        a = mr[(mr.group == "tagged") & (mr.outcome == outcome)].iloc[0]
        b = mr[(mr.group == "untagged") & (mr.outcome == outcome)].iloc[0]
        d, lo, hi = newcombe(int(a.x), int(a.n), int(b.x), int(b.n))
        an = res[f"newcombe_{outcome}_tagged_minus_untagged"]
        print(f"NEWCOMBE {outcome}: mine diff={100 * d:.3f} CI [{100 * lo:.3f}, {100 * hi:.3f}] pp; "
              f"analyst {100 * an['diff']:.3f} [{100 * an['lo']:.3f}, {100 * an['hi']:.3f}]")
        assert abs(d - an["diff"]) < 1e-9 and abs(lo - an["lo"]) < 1e-6 and abs(hi - an["hi"]) < 1e-6
    from scipy.stats import binomtest
    for _, r in mr.iterrows():
        ci = binomtest(int(r.x), int(r.n)).proportion_ci(0.95, method="wilson")
        assert abs(100 * ci.low - r.ci_lo_pct) < 0.01 and abs(100 * ci.high - r.ci_hi_pct) < 0.01
        assert abs(100 * r.x / r.n - r.rate_pct) < 0.01
    print("WILSON CIs in match_rate.csv agree with scipy for all", len(mr), "rows")
    cov = pd.read_csv(Q / "coverage_by_half.csv")
    for _, r in cov.iterrows():
        n1, n2 = int(r.n_tagged), int(r.n_untagged)
        x1, x2 = round(r.keys_labelled_rate_tagged * n1), round(r.keys_labelled_rate_untagged * n2)
        d, lo, hi = newcombe(x1, n1, x2, n2)
        print(f"NEWCOMBE {r.half}: mine {100 * d:.1f} [{100 * lo:.1f}, {100 * hi:.1f}] analyst "
              f"{100 * r.diff_tagged_minus_untagged:.1f} [{100 * r.diff_ci_lo:.1f}, {100 * r.diff_ci_hi:.1f}]")
        # analyst CSV is rounded to 3 decimals
        assert abs(d - r.diff_tagged_minus_untagged) < 1e-3 and abs(lo - r.diff_ci_lo) < 2e-3 and abs(hi - r.diff_ci_hi) < 2e-3
