"""Validator: rebuild the key x half matrix, labels and shares by an independent route and compare with the
analyst's outputs; independent bootstrap; label spot check against title.basics.

Reuse (NOT independent, flagged in 06_validation.md): pipeline.load/clean (cleaning, keys) and
pipeline.label (IMDb matching) are called to obtain the cleaned keys and the analyst's labels. Everything
after that (hours matrix, top-10, new/carried, shares, margins, bootstrap, group mapping) is my own code.

Run (slow, several minutes): pytest -q -s tests/test_validation_rebuild.py
"""
import math
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
Q = ROOT / "outputs" / "q1"
HALVES = ["H1 2023", "H2 2023", "H1 2024", "H2 2024", "H1 2025", "H2 2025", "H1 2026"]


@pytest.fixture(scope="module")
def built():
    import json
    from pipeline import clean, label, load

    raw = load.load_reports()
    cl = clean.clean_reports(raw)
    scope = json.loads((Q / "scope.json").read_text())
    in_scope = clean.scope_keys(cl.half_keys, scope["target"], id_col="kid")
    union = sorted(set().union(*in_scope.values()))
    ki = cl.key_info.set_index("kid")
    mapping = label.load_mapping(ROOT / "config" / "genre_mapping.csv")
    basics, genres = load.load_basics(load.IMDB_DIR / "title.basics.tsv.gz", label.ALL_TYPES)
    miss = label.check_genres_covered(genres, mapping)
    votes = load.load_votes(load.IMDB_DIR / "title.ratings.tsv.gz")
    needed = {label.norm_title(s) for k in union for s in ki.at[k, "segments"]}
    idx = label.ImdbIndex(basics, votes, needed)
    idx.add_akas(load.IMDB_DIR / "title.akas.tsv.gz", needed)
    lab = label.label_keys(ki, union, idx, mapping).set_index("kid").loc[union]
    return dict(cl=cl, union=union, in_scope=in_scope, ki=ki, mapping=mapping, basics=basics, votes=votes,
                lab=lab, missing_genres=miss, scope=scope)


# ---------------------------------------------------------------- scope (own implementation)
def own_scope(hk, target):
    keys = set()
    for h in HALVES:
        d = hk[hk.half == h].sort_values(["hours", "kid"], ascending=[False, True])
        cum = d["hours"].cumsum() / d["hours"].sum()
        # smallest prefix whose cumulative share reaches the target
        n = int((cum < target - 1e-12).sum()) + 1
        keys |= set(d["kid"].iloc[:n])
    return keys


def test_scope_union(built):
    hk = built["cl"].half_keys
    mine = own_scope(hk, 0.80)
    theirs = set(built["union"])
    print(f"SCOPE union: mine={len(mine)} analyst={len(theirs)} symmetric diff={len(mine ^ theirs)}")
    # ties at the cut can differ by tie-break; report the size of the difference
    assert len(mine ^ theirs) <= 10


def test_genre_mapping_independent(built):
    lab, mp = built["lab"], built["mapping"]
    look = {}
    for r in mp.itertuples():
        if r.group != "" and not pd.isna(r.group_priority):
            look[r.imdb_genre] = (r.group_priority, r.group)
    bad = 0
    for k, r in lab.iterrows():
        g = r.imdb_genres
        mine = None
        if isinstance(g, str):
            c = [look[x] for x in g.split(",") if x in look]
            mine = min(c)[1] if c else None
        if (mine or None) != (r.group if isinstance(r.group, str) else None):
            bad += 1
    print("GROUP MAPPING mismatches (priority rule re-implemented):", bad, "of", len(lab))
    print("Genres in title.basics missing from mapping:", built["missing_genres"])
    assert bad == 0 and not built["missing_genres"]


# ---------------------------------------------------------------- matrices and shares
def own_matrices(built):
    hk = built["cl"].half_keys
    union = built["union"]
    lab = built["lab"]
    hours = {(r.kid, r.half): r.hours for r in hk.itertuples()}
    key_of = dict(zip(hk["kid"], hk["key"]))
    H = np.array([[hours.get((k, h), 0.0) for h in HALVES] for k in union])
    top10 = np.zeros(H.shape, bool)
    pos = {k: i for i, k in enumerate(union)}
    for t, h in enumerate(HALVES):
        d = hk[hk.half == h]
        order = sorted(zip(d["hours"], d["kid"]), key=lambda x: (-x[0], x[1]))[:10]
        for _, k in order:
            top10[pos[k], t] = True
    present_prev = {}
    titles_by_half = {h: set(hk.loc[hk.half == h, "key"]) for h in HALVES}
    kids_by_half = {h: set(hk.loc[hk.half == h, "kid"]) for h in HALVES}
    new = np.zeros(H.shape, bool)
    car = np.zeros(H.shape, bool)
    for t in range(1, 7):
        for k, i in pos.items():
            if H[i, t] <= 0:
                continue
            if t == 1:
                prev = key_of[k] in titles_by_half[HALVES[0]]
            else:
                prev = k in kids_by_half[HALVES[t - 1]]
            (car if prev else new)[i, t] = True
    labelled = lab["labelled"].to_numpy()
    groups = lab["group"].to_numpy()
    return H, top10, new, car, labelled, groups


def shares(H, grp, glist, mask):
    out = np.full((len(glist), 7), np.nan)
    for t in range(7):
        w = np.where(mask[:, t], H[:, t], 0.0)
        tot = w.sum()
        if tot == 0:
            continue
        for gi, g in enumerate(glist):
            out[gi, t] = 100 * w[grp == g].sum() / tot
    return out


def test_shares_rebuilt(built):
    H, top10, new, car, labelled, groups = own_matrices(built)
    H, top10, new, car, groups = H[labelled], top10[labelled], new[labelled], car[labelled], groups[labelled]
    df = pd.read_csv(Q / "shares_all_variants.csv")
    glist = sorted(df.genre.unique())
    variants = {"c1": np.ones_like(top10), "c2": ~top10, "c3n": new, "c3c": car}
    worst = 0
    for v, mk in variants.items():
        S = shares(H, groups, glist, mk)
        for gi, g in enumerate(glist):
            theirs = df[(df.variant == v) & (df.genre == g)].set_index("half").loc[HALVES, "share_pct"].to_numpy()
            both = ~np.isnan(S[gi]) & ~np.isnan(theirs)
            assert (np.isnan(S[gi]) == np.isnan(theirs)).all()
            worst = max(worst, np.abs(S[gi][both] - theirs[both]).max())
    print("SHARES rebuilt: max abs diff over 4 variants x 8 genres x 7 halves (pp):", worst)
    assert worst < 1e-6
    vh = pd.read_csv(Q / "variant_hours.csv").set_index("variant")
    for v, mk in variants.items():
        mine = (H * mk).sum(axis=0)
        d = np.abs(mine - vh.loc[v, HALVES].to_numpy(float)).max()
        print(f"VARIANT HOURS {v}: max abs diff {d}")
        assert d < 1
    # unlabelled / coverage numbers
    Hall, _, _, _, lb, _ = own_matrices(built)
    cov = pd.read_csv(Q / "coverage_by_half.csv")
    for t, h in enumerate(HALVES):
        ins = Hall[:, t].sum()
        lab_h = Hall[lb, t].sum()
        mine_unl = 100 * (ins - lab_h) / ins
        theirs = float(cov.loc[cov.half == h, "unlabelled_over_inscope_pct"].iloc[0])
        print(f"COVERAGE {h}: unlabelled/in-scope mine={mine_unl:.3f} analyst={theirs:.3f}; in-scope hours mine={ins:.0f}")
        assert abs(mine_unl - theirs) < 1e-2
    print("TOP10 cells in unlabelled keys:", int(own_matrices(built)[1][~lb].sum()))


# ---------------------------------------------------------------- independent bootstrap
def margin_set(H, grp, glist, top10, new, car):
    res = {}
    for v, mk in (("c1", np.ones_like(top10)), ("c2", ~top10), ("c3n", new), ("c3c", car)):
        res[v] = shares(H, grp, glist, mk)
    return res


def aligned(S, start_pos, sign):
    d = S[:, 1:] - S[:, :-1]
    pos = np.arange(start_pos, start_pos + d.shape[1])
    sg = np.where(pos % 2 == 0, 1.0, -1.0) * sign
    return d * sg


def test_independent_bootstrap(built):
    H, top10, new, car, labelled, groups = own_matrices(built)
    H, top10, new, car, groups = H[labelled], top10[labelled], new[labelled], car[labelled], groups[labelled]
    gr = pd.read_csv(Q / "genre_results.csv")
    glist = sorted(set(groups))
    # integer group codes for a fast bootstrap
    code = np.array([glist.index(g) for g in groups])
    G = np.zeros((len(code), len(glist)))
    G[np.arange(len(code)), code] = 1
    elig = [glist.index(g) for g in gr.genre]
    sign = np.array([1.0 if d == "up" else -1.0 for d in gr.direction])
    rng = np.random.default_rng(20261112)  # different seed AND different draw method (integer indices)
    n = len(H)
    B = 2000
    c1m = np.empty((B, len(elig)))
    mean_al = np.empty((B, len(elig)))
    c2m = np.empty((B, len(elig)))
    gm = np.empty((B, len(elig)))
    for b in range(B):
        ix = rng.integers(0, n, n)
        cnt = np.bincount(ix, minlength=n).astype(float)

        def sh(mask):
            num = G.T @ (H * mask * cnt[:, None])
            return 100 * num / num.sum(axis=0)

        S1, S2 = sh(np.ones_like(top10)), sh(~top10)
        S3n, S3c = sh(new), sh(car)
        a1 = aligned(S1, 0, 1.0)[elig] * sign[:, None]
        a2 = aligned(S2, 0, 1.0)[elig] * sign[:, None]
        a3n = aligned(S3n[:, 1:], 1, 1.0)[elig] * sign[:, None]
        a3c = aligned(S3c[:, 1:], 1, 1.0)[elig] * sign[:, None]
        c1m[b], c2m[b] = a1.min(1), a2.min(1)
        mean_al[b] = a1.mean(1)
        gm[b] = np.minimum.reduce([a1.min(1), a2.min(1), a3n.min(1), a3c.min(1)])
    lo = lambda x: np.percentile(x, 2.5, axis=0)
    hi = lambda x: np.percentile(x, 97.5, axis=0)
    rows = []
    for e, g in enumerate(gr.genre):
        r = gr.iloc[e]
        rows.append((g, "mean_aligned", r.mean_aligned_shift_pp, lo(mean_al)[e], hi(mean_al)[e], r.mean_aligned_ci_lo, r.mean_aligned_ci_hi))
        rows.append((g, "margin_c1", r.margin_c1, lo(c1m)[e], hi(c1m)[e], r.margin_c1_ci_lo, r.margin_c1_ci_hi))
        rows.append((g, "margin_c2", r.margin_c2, lo(c2m)[e], hi(c2m)[e], r.margin_c2_ci_lo, r.margin_c2_ci_hi))
        rows.append((g, "genre_margin", r.genre_margin_pp, lo(gm)[e], hi(gm)[e], r.genre_margin_ci_lo, r.genre_margin_ci_hi))
        print(f"BOOT {g:24s} {rows[-4][1]:13s} mine [{rows[-4][3]:7.2f},{rows[-4][4]:7.2f}] analyst [{rows[-4][5]:7.2f},{rows[-4][6]:7.2f}]"
              f" | {rows[-3][1]} mine [{rows[-3][3]:7.2f},{rows[-3][4]:7.2f}] analyst [{rows[-3][5]:7.2f},{rows[-3][6]:7.2f}]"
              f" | {rows[-2][1]} mine [{rows[-2][3]:7.2f},{rows[-2][4]:7.2f}] analyst [{rows[-2][5]:7.2f},{rows[-2][6]:7.2f}]"
              f" | {rows[-1][1]} mine [{rows[-1][3]:7.2f},{rows[-1][4]:7.2f}] analyst [{rows[-1][5]:7.2f},{rows[-1][6]:7.2f}]")
        print(f"BOOTPASS {g}: theta2 mine={float((gm[:, e] >= 2 - 1e-9).mean()):.4f} analyst={r['boot_pass_frac_theta_2.0']:.4f}; "
              f"theta1.5 mine={float((gm[:, e] >= 1.5 - 1e-9).mean()):.4f} analyst={r['boot_pass_frac_theta_1.5']:.4f}")
    worst = max(max(abs(r[3] - r[5]), abs(r[4] - r[6])) for r in rows)
    print("BOOT worst endpoint difference (pp):", worst)
    # analyst's point estimates inside my intervals?
    inside = sum(1 for r in rows if r[3] <= r[2] <= r[4])
    print(f"BOOT analyst point estimate inside my 95% CI: {inside}/{len(rows)}")
    # not asserted tightly: reported in 06_validation.md


# ---------------------------------------------------------------- sensitivity and influence
def test_drama_and_influence(built):
    H, top10, new, car, labelled, groups = own_matrices(built)
    keys = np.array(built["union"])
    Hl, tl, nl, cl_, gl, kl = H[labelled], top10[labelled], new[labelled], car[labelled], groups[labelled], keys[labelled]
    glist = sorted(set(gl))
    S = margin_set(Hl, gl, glist, tl, nl, cl_)
    gi = glist.index("Drama")
    best = -math.inf
    for sign in (1.0, -1.0):
        ms = [
            (aligned(S["c1"], 0, 1.0)[gi] * sign).min(), (aligned(S["c2"], 0, 1.0)[gi] * sign).min(),
            (aligned(S["c3n"][:, 1:], 1, 1.0)[gi] * sign).min(), (aligned(S["c3c"][:, 1:], 1, 1.0)[gi] * sign).min()]
        print("DRAMA sign", sign, "margins c1,c2,c3n,c3c", [round(float(m), 3) for m in ms])
        best = max(best, min(ms))
    print("DRAMA mean share", S["c1"][gi].mean(), "best genre margin", best)
    # influence: Sci-Fi & Fantasy H1 2025 -> H2 2025 (+4.86 pp claimed)
    sf = glist.index("Sci-Fi & Fantasy")
    print("SCI-FI shares c1:", np.round(S["c1"][sf], 3))
    print("SCI-FI shift H1 2025->H2 2025:", S["c1"][sf][5] - S["c1"][sf][4])
    mask = gl == "Sci-Fi & Fantasy"
    d = Hl[mask][:, 5] - Hl[mask][:, 4]
    top = np.argsort(-np.abs(d))[:6]
    for i in top:
        print("  SCIFI key", kl[mask][i], "hours H1 2025", Hl[mask][i, 4], "H2 2025", Hl[mask][i, 5])
    # leave-top-3-out per half robustness for the largest genre swing
    for drop in (10, 25):
        mk = np.ones_like(tl)
        for t in range(7):
            o = np.argsort(-Hl[:, t])[:drop]
            mk[o, t] = False
        S2 = shares(Hl, gl, glist, mk)
        best_by_genre = {}
        for g in glist:
            a = aligned(S2, 0, 1.0)[glist.index(g)]
            best_by_genre[g] = round(float(max(a.min(), (-a).min())), 3)
        print(f"DROP TOP-{drop} per half, check-1 best margins:", best_by_genre)


# ---------------------------------------------------------------- label spot check
def simple_norm(s):
    s = unicodedata.normalize("NFKD", str(s).casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^0-9a-z\u0080-￿]+", "", s)


def test_label_spot_check(built):
    lab, ki, basics, votes, mp = built["lab"], built["ki"], built["basics"], built["votes"], built["mapping"]
    look = {r.imdb_genre: (r.group_priority, r.group) for r in mp.itertuples() if r.group != "" and not pd.isna(r.group_priority)}
    rng = np.random.default_rng(99)
    sample = rng.choice(np.array(lab.index), 400, replace=False)
    need = {simple_norm(ki.at[k, "segments"][0]) for k in sample}
    b = basics
    p = b["primaryTitle"].fillna("").map(simple_norm)
    sel = b[p.isin(need)].copy()
    sel["n"] = p[p.isin(need)]
    sel["votes"] = sel["tconst"].map(votes).fillna(0)
    by = {n: g for n, g in sel.groupby("n")}
    agree = dis = nomatch_mine = 0
    detail = []
    for k in sample:
        r = lab.loc[k]
        if not r["labelled"] or r["stage"] != "stage1":
            continue
        seg = simple_norm(ki.at[k, "segments"][0])
        kt = ki.at[k, "type_known"]
        cand = by.get(seg)
        if cand is None:
            nomatch_mine += 1
            continue
        types = {"film": {"movie", "tvMovie", "tvSpecial"}, "series": {"tvSeries", "tvMiniSeries"}}.get(kt)
        if types is not None:
            cand = cand[cand.titleType.isin(types)]
        if cand.empty:
            nomatch_mine += 1
            continue
        top = cand.sort_values(["votes", "tconst"], ascending=[False, True]).iloc[0]
        c = [look[x] for x in str(top.genres).split(",") if x in look]
        mg = min(c)[1] if c else None
        if mg == r["group"]:
            agree += 1
        else:
            dis += 1
            detail.append((k, r["group"], mg, int(r["candidates"]), top.primaryTitle))
    tot = agree + dis
    print(f"LABEL SPOT CHECK (stage-1 labelled keys in a random 400, simple exact-title/max-votes, no year filter): "
          f"agree={agree} disagree={dis} not-comparable={nomatch_mine} agreement={100 * agree / max(tot, 1):.1f}%")
    for d_ in detail[:15]:
        print("  DISAGREE", d_)
