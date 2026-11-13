"""Full-scope run of the approved plan: labelling, coverage, Q1 checks, bootstrap, permutation,
sensitivity, charts. Orchestration only; the maths lives in analyze.py, the figures in visualize.py.

Gate: refuses to run without workflow/05_pilot_check.md (the human's pilot hand check).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import analyze as an
from pipeline import clean, label, load, visualize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "q1"
SEED = 42
N_BOOT = 2000
MAX_KEYS = 4500
THETA = 2.0
THETAS = (1.5, 2.0, 3.0)
COVERAGE_LIMIT = 0.10  # plan P5: unlabelled > 10% of in-scope hours in any half -> inconclusive
ELIGIBLE_MIN_MEAN = 5.0


def _save_fig(fig, name: str, df: pd.DataFrame) -> None:
    """PNG plus the aggregated data behind it (same stem, CSV) for the website."""
    fig.savefig(OUT / f"{name}.png", dpi=130)
    df.to_csv(OUT / f"{name}.csv", index=False)
    import matplotlib.pyplot as plt
    plt.close(fig)


def _labels(cl, in_scope_union, ki, cache_dir):
    cache = Path(cache_dir) / "key_labels.pkl" if cache_dir else None
    if cache and cache.exists():
        print("labels from cache", cache)
        return pd.read_pickle(cache)
    mapping = label.load_mapping(ROOT / "config" / "genre_mapping.csv")
    basics, genres = load.load_basics(load.IMDB_DIR / "title.basics.tsv.gz", label.ALL_TYPES)
    missing = label.check_genres_covered(genres, mapping)
    if missing:
        print("STOP: genres missing from mapping:", missing)
        sys.exit(4)
    votes = load.load_votes(load.IMDB_DIR / "title.ratings.tsv.gz")
    needed = {label.norm_title(s) for k in in_scope_union for s in ki.at[k, "segments"]}
    idx = label.ImdbIndex(basics, votes, needed)
    print("akas hits loaded:", idx.add_akas(load.IMDB_DIR / "title.akas.tsv.gz", needed))
    lab = label.label_keys(ki, in_scope_union, idx, mapping)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        lab.to_pickle(cache)
    return lab


def stage_full() -> None:
    if not (ROOT / "workflow" / "05_pilot_check.md").exists() and not (ROOT / "workflow" / "05_pilot_check").exists():
        print("STOP: workflow/05_pilot_check.md is missing (pilot gate).")
        sys.exit(6)
    OUT.mkdir(parents=True, exist_ok=True)
    halves = load.HALF_LABELS
    T = len(halves)
    res: dict = {"run_date": str(date.today()), "seed": SEED, "n_boot": N_BOOT}

    # ------------------------------------------------------------------ clean + scope (P1, P2, P4)
    raw = load.load_reports()
    cl = clean.clean_reports(raw)
    scope = json.loads((OUT / "scope.json").read_text())
    in_scope = clean.scope_keys(cl.half_keys, scope["target"], id_col="kid")
    union = sorted(set().union(*in_scope.values()))
    assert len(union) == scope["union_keys"] <= MAX_KEYS, "scope changed since the pilot: stop and ask"
    ki = cl.key_info.set_index("kid")

    # ------------------------------------------------------------------ labelling (P3)
    lab = _labels(cl, union, ki, os.environ.get("Q1_CACHE")).set_index("kid").loc[union]
    res["labelling"] = {
        "keys": len(lab), "matched": int(lab["matched"].sum()), "labelled": int(lab["labelled"].sum()),
        "stage_counts": lab["stage"].fillna("none").value_counts().to_dict(),
        "tie_break_counts": lab["tie_break"].fillna("none").value_counts().to_dict(),
        "ambiguous_keys_candidates_gt1": int((lab["candidates"] > 1).sum()),
    }
    print("LABELLING", json.dumps(res["labelling"]))

    # ------------------------------------------------------------------ matrices
    H_all, top10_all, new_all, carried_all = an.build_matrices(cl.half_keys, halves, union)
    tagged = lab["tagged"].to_numpy()
    labelled = lab["labelled"].to_numpy()

    # ------------------------------------------------------------------ coverage and bias (P5)
    other = cl.log["other_hours_by_half"]
    listed = cl.half_keys.groupby("half")["hours"].sum()
    rows = []
    for t, h in enumerate(halves):
        ins = H_all[:, t].sum()
        labh = H_all[labelled, t].sum()
        row = {"half": h, "all_listed_hours": float(listed[h] + other.get(h, 0.0)), "in_scope_hours": float(ins),
               "labelled_hours": float(labh), "unlabelled_in_scope_hours": float(ins - labh),
               "labelled_over_all_pct": 100 * labh / (listed[h] + other.get(h, 0.0)),
               "labelled_over_inscope_pct": 100 * labh / ins, "unlabelled_over_inscope_pct": 100 * (ins - labh) / ins,
               "hours_not_in_scope_pct_of_listed": 100 * (1 - ins / (listed[h] + other.get(h, 0.0)))}
        for nm, mk in (("tagged", tagged), ("untagged", ~tagged)):
            row[f"labelled_over_inscope_pct_{nm}"] = 100 * H_all[mk & labelled, t].sum() / H_all[mk, t].sum()
        # key-level counts for the Newcombe difference (keys present in that half)
        pres = H_all[:, t] > 0
        x1, n1 = int((labelled & tagged & pres).sum()), int((tagged & pres).sum())
        x2, n2 = int((labelled & ~tagged & pres).sum()), int((~tagged & pres).sum())
        d, lo, hi = an.newcombe_diff(x1, n1, x2, n2)
        row.update({"keys_labelled_rate_tagged": x1 / n1, "keys_labelled_rate_untagged": x2 / n2,
                    "diff_tagged_minus_untagged": d, "diff_ci_lo": lo, "diff_ci_hi": hi, "n_tagged": n1, "n_untagged": n2})
        rows.append(row)
    cov = pd.DataFrame(rows)
    cov.to_csv(OUT / "coverage_by_half.csv", index=False)
    print(cov.round(3).to_string())
    res["coverage_rule_inconclusive"] = bool((cov["unlabelled_over_inscope_pct"] > 100 * COVERAGE_LIMIT).any())
    res["max_unlabelled_over_inscope_pct"] = float(cov["unlabelled_over_inscope_pct"].max())

    match_rows = []
    for nm, mk in (("all", np.ones_like(tagged)), ("tagged", tagged), ("untagged", ~tagged)):
        for what, vec in (("matched", lab["matched"].to_numpy()), ("labelled", labelled)):
            x, n = int(vec[mk].sum()), int(mk.sum())
            lo, hi = an._wilson(x, n)
            match_rows.append({"group": nm, "outcome": what, "x": x, "n": n, "rate_pct": 100 * x / n,
                               "ci_lo_pct": 100 * lo, "ci_hi_pct": 100 * hi})
    match = pd.DataFrame(match_rows)
    for what in ("matched", "labelled"):
        a = match[(match.group == "tagged") & (match.outcome == what)].iloc[0]
        b = match[(match.group == "untagged") & (match.outcome == what)].iloc[0]
        d, lo, hi = an.newcombe_diff(int(a.x), int(a.n), int(b.x), int(b.n))
        res[f"newcombe_{what}_tagged_minus_untagged"] = {"diff": d, "lo": lo, "hi": hi}
    match.to_csv(OUT / "match_rate.csv", index=False)
    print(match.round(2).to_string())
    print("newcombe", res["newcombe_matched_tagged_minus_untagged"], res["newcombe_labelled_tagged_minus_untagged"])

    # hours-weighted coarse-group check requested in the pilot decision
    lk = lab[labelled]
    hrs_lab = H_all[labelled].sum(axis=1)
    res["group_differs_from_first_genre"] = {
        "keys_pct": float(100 * lk["group_differs_first"].mean()),
        "hours_pct": float(100 * hrs_lab[lk["group_differs_first"].to_numpy()].sum() / hrs_lab.sum()),
    }
    print("coarse group", res["group_differs_from_first_genre"])

    # ------------------------------------------------------------------ variants on labelled keys
    mapping = label.load_mapping(ROOT / "config" / "genre_mapping.csv")
    groups = list(dict.fromkeys(mapping.dropna(subset=["group_priority"]).sort_values("group_priority")["group"]))
    gi = lab.loc[labelled, "group"].map({g: i for i, g in enumerate(groups)}).to_numpy()
    G = np.zeros((len(gi), len(groups)))
    G[np.arange(len(gi)), gi] = 1
    H, top10, new, carried = H_all[labelled], top10_all[labelled], new_all[labelled], carried_all[labelled]
    # top-10 keys must not be unlabelled-only artefacts: report how many top-10 cells are unlabelled
    res["top10_cells_unlabelled"] = int(top10_all[~labelled].sum())
    v = an.variant_shares(H, G, top10, new, carried)
    m = an.variant_margins(v)
    gm, gdir = an.genre_margin(m)
    mean_share = v.c1.mean(axis=1)
    eligible = np.flatnonzero(mean_share >= ELIGIBLE_MIN_MEAN)
    res["eligible_genres"] = [groups[i] for i in eligible]
    res["mean_share_pct"] = {groups[i]: float(mean_share[i]) for i in range(len(groups))}
    direction = gdir[eligible]
    print("eligible", res["eligible_genres"])

    # all shares, all variants (aggregated, for the web)
    sh_rows = []
    for nm in an.CHECKS:
        S = getattr(v, nm)
        for gidx, g in enumerate(groups):
            for t, h in enumerate(halves):
                sh_rows.append({"variant": nm, "genre": g, "half": h, "share_pct": S[gidx, t]})
    pd.DataFrame(sh_rows).to_csv(OUT / "shares_all_variants.csv", index=False)
    cnt = []
    for nm, mk in (("c1", np.ones_like(top10)), ("c2", ~top10), ("c3n", new), ("c3c", carried)):
        cnt.append({"variant": nm, **{h: float((H * mk)[:, t].sum()) for t, h in enumerate(halves)}})
    pd.DataFrame(cnt).to_csv(OUT / "variant_hours.csv", index=False)

    # ------------------------------------------------------------------ bootstrap
    bs = an.cluster_bootstrap(H, G, top10, new, carried, eligible, direction, n_boot=N_BOOT, seed=SEED)
    sgn = np.where(direction == 0, 1.0, -1.0)[:, None] * an.SIGN_UP[None, :]
    D1 = an.shifts(v.c1)
    trans = [f"{halves[i]} -> {halves[i + 1]}" for i in range(T - 1)]

    def row_for(thetas):
        return {f"pass_theta_{t}": gm >= t - an.TOL for t in thetas}

    passes = row_for(THETAS)
    glo, ghi = an.pct_ci(bs["gmargin"])
    mlo, mhi = an.pct_ci(bs["mean_aligned"])
    clo, chi = an.pct_ci(bs["check_margin"])
    slo, shi = an.pct_ci(bs["shift"])
    gr_rows = []
    for e, i in enumerate(eligible):
        r = {"genre": groups[i], "mean_share_pct": mean_share[i], "direction": "up" if direction[e] == 0 else "down",
             "genre_margin_pp": gm[i], "genre_margin_ci_lo": glo[e], "genre_margin_ci_hi": ghi[e],
             "mean_aligned_shift_pp": float((D1[i] * sgn[e]).mean()), "mean_aligned_ci_lo": mlo[e], "mean_aligned_ci_hi": mhi[e]}
        for k, nm in enumerate(an.CHECKS):
            r[f"margin_{nm}"] = m[nm][i, direction[e]]
            r[f"margin_{nm}_ci_lo"], r[f"margin_{nm}_ci_hi"] = clo[e, k], chi[e, k]
        for nm in ("c3n", "c3c"):
            S = getattr(v, nm)
            r[f"mean_aligned_shift_{nm}_5trans"] = float((an.shifts(S[:, 1:])[i] * sgn[e][1:]).mean())
        for t in THETAS:
            r[f"pass_theta_{t}"] = bool(passes[f"pass_theta_{t}"][i])
            r[f"boot_pass_frac_theta_{t}"] = float((bs["gmargin"][:, e] >= t - an.TOL).mean())
        r["near_miss_theta_2"] = bool(THETA - an.NEAR <= gm[i] < THETA - an.TOL)
        for j in range(6):
            r[f"shift_{j + 1}"] = D1[i, j]
        gr_rows.append(r)
    gr = pd.DataFrame(gr_rows)
    gr.to_csv(OUT / "genre_results.csv", index=False)
    print(gr.round(2).T.to_string())

    # ------------------------------------------------------------------ permutation
    perm1, M1 = an.permutation_test(v, eligible, THETAS, fix_first=False)
    perm_all, Mall = an.permutation_test(v, eligible, THETAS, fix_first=True)
    res["permutation_check1_only"], res["permutation_all_checks"] = perm1, perm_all
    res["single_genre_reference_pct"] = 100 * 2 * 0.5 ** 6
    print("PERM check1", json.dumps(perm1))
    print("PERM all", json.dumps(perm_all))

    # ------------------------------------------------------------------ pair rule + sensitivity
    res["pass"] = {}
    for t in THETAS:
        pg = [e for e, i in enumerate(eligible) if gm[i] >= t - an.TOL]
        names = [groups[eligible[e]] for e in pg]
        entry = {"passing_genres": names, "n_passing": len(names)}
        if len(pg) >= 2:
            comps, pairs = an.pair_rule(np.array([D1[eligible[e]] for e in pg]), names)
            entry.update({"findings_after_pair_rule": len(comps), "groups": comps, "pairs": pairs})
        else:
            entry["findings_after_pair_rule"] = len(pg)
        res["pass"][str(t)] = entry
    res["near_misses_theta_2"] = [groups[i] for e, i in enumerate(eligible) if THETA - an.NEAR <= gm[i] < THETA - an.TOL]

    # post-stratification of check 1 by tagged/untagged coverage (sensitivity b)
    W = np.ones_like(H)
    ins_all = H_all
    tg = tagged[labelled]
    for t in range(T):
        for mk_all, mk_lab in ((tagged, tg), (~tagged, ~tg)):
            W[mk_lab, t] = ins_all[mk_all, t].sum() / H[mk_lab, t].sum()
    Sps = an.group_shares(H, G, weights=W)
    ps_up, ps_dn = an.margins(an.shifts(Sps))
    ps = pd.DataFrame({"genre": [groups[i] for i in eligible], "check1_margin_up": ps_up[eligible], "check1_margin_down": ps_dn[eligible],
                       "check1_margin_unweighted_best": [m["c1"][i].max() for i in eligible]})
    for t in THETAS:
        ps[f"check1_pass_theta_{t}_poststrat"] = np.maximum(ps_up[eligible], ps_dn[eligible]) >= t - an.TOL
        ps[f"check1_pass_theta_{t}_plain"] = ps["check1_margin_unweighted_best"].to_numpy() >= t - an.TOL
    ps.to_csv(OUT / "sensitivity_poststrat.csv", index=False)
    print(ps.round(2).to_string())

    # ------------------------------------------------------------------ charts
    elig_names = [groups[i] for i in eligible]
    c1 = pd.DataFrame([{"genre": groups[i], "half": h, "share_pct": v.c1[i, t]} for i in eligible for t, h in enumerate(halves)])
    _save_fig(visualize.plot_share_lines(c1), "chart1_share_lines", c1)
    c2 = pd.DataFrame([{"genre": groups[i], "transition": trans[j], "shift_pp": D1[i, j], "ci_lo": slo[e, j], "ci_hi": shi[e, j]}
                       for e, i in enumerate(eligible) for j in range(6)])
    _save_fig(visualize.plot_shift_bars(c2, THETA), "chart2_shift_bars", c2)
    c3 = pd.DataFrame([{"genre": groups[i], "direction": "up" if direction[e] == 0 else "down", "check": nm,
                        "margin_pp": m[nm][i, direction[e]], "ci_lo": clo[e, k], "ci_hi": chi[e, k],
                        "pass_at_theta": bool(m[nm][i, direction[e]] >= THETA - an.TOL)}
                       for e, i in enumerate(eligible) for k, nm in enumerate(an.CHECKS)])
    _save_fig(visualize.plot_check_matrix(c3, THETA), "chart3_check_matrix", c3)
    _save_fig(visualize.plot_perm_null(M1, perm1["observed_M"], THETA, "Permutation null, check 1 only (7! = 5,040 orderings)"),
              "chart4a_perm_null_check1", pd.DataFrame({"M": M1}).value_counts().rename("n").reset_index())
    _save_fig(visualize.plot_perm_null(Mall, perm_all["observed_M"], THETA, "Permutation null, all checks (H1 2023 fixed, 6! = 720 orderings)"),
              "chart4b_perm_null_all", pd.DataFrame({"M": Mall}).value_counts().rename("n").reset_index())
    _save_fig(visualize.plot_coverage(cov, match[match.outcome == "matched"]), "chart5_coverage_match",
              cov[["half", "labelled_over_inscope_pct", "labelled_over_all_pct"]])
    passing = [e for e, i in enumerate(eligible) if gm[i] >= THETA - an.TOL]
    if passing:
        pr = pd.DataFrame([{"genre": groups[eligible[e]], "direction": "up" if direction[e] == 0 else "down",
                            "expected_shift_H1_2026_to_H2_2026_pp": float(sgn[e][0] * gr.loc[e, "mean_aligned_shift_pp"]),
                            "ci_lo": float(sgn[e][0] * (mlo[e] if sgn[e][0] > 0 else mhi[e])),
                            "ci_hi": float(sgn[e][0] * (mhi[e] if sgn[e][0] > 0 else mlo[e])),
                            "date_written": str(date.today())} for e in passing])
        pr.to_csv(OUT / "chart6_h2_2026_prediction.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(res, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    print("DONE; results.json written; passing at theta 2:", res["pass"]["2.0"])
