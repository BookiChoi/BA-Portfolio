"""Validator: bootstrap of the genre margin with the direction re-chosen in every replicate
(plan: genre margin = max over direction of min over the four checks), compared with genre_results.csv.
Reuses the fixtures of test_validation_rebuild.py (cleaning and labels are the analyst's code)."""
import numpy as np
import pandas as pd
from test_validation_rebuild import Q, aligned, built, own_matrices  # noqa: F401


def test_bootstrap_free_direction(built):  # noqa: F811
    H, top10, new, car, labelled, groups = own_matrices(built)
    H, top10, new, car, groups = H[labelled], top10[labelled], new[labelled], car[labelled], groups[labelled]
    gr = pd.read_csv(Q / "genre_results.csv")
    glist = sorted(set(groups))
    code = np.array([glist.index(g) for g in groups])
    G = np.zeros((len(code), len(glist)))
    G[np.arange(len(code)), code] = 1
    elig = [glist.index(g) for g in gr.genre]
    rng = np.random.default_rng(777)
    n, B = len(H), 2000
    out = np.empty((B, len(elig)))
    for b in range(B):
        cnt = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)

        def sh(mask):
            num = G.T @ (H * mask * cnt[:, None])
            with np.errstate(invalid="ignore", divide="ignore"):
                return 100 * num / num.sum(axis=0)

        a = [aligned(sh(np.ones_like(top10)), 0, 1.0), aligned(sh(~top10), 0, 1.0),
             aligned(sh(new)[:, 1:], 1, 1.0), aligned(sh(car)[:, 1:], 1, 1.0)]
        best = []
        for sign in (1.0, -1.0):
            best.append(np.minimum.reduce([(x[elig] * sign).min(1) for x in a]))
        out[b] = np.maximum(best[0], best[1])
    lo, hi = np.percentile(out, 2.5, axis=0), np.percentile(out, 97.5, axis=0)
    worst = 0
    for e, g in enumerate(gr.genre):
        r = gr.iloc[e]
        worst = max(worst, abs(lo[e] - r.genre_margin_ci_lo), abs(hi[e] - r.genre_margin_ci_hi))
        print(f"GMARGIN-BOOT {g:24s} mine [{lo[e]:7.2f},{hi[e]:7.2f}] analyst [{r.genre_margin_ci_lo:7.2f},{r.genre_margin_ci_hi:7.2f}] "
              f"pass2 frac mine={(out[:, e] >= 2 - 1e-9).mean():.4f}")
    print("GMARGIN-BOOT worst endpoint difference (pp):", worst)
