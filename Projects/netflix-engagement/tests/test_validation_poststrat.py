"""Validator: post-stratification sensitivity (check 1 reweighted so labelled hours per language group match the
in-scope hours of that group) recomputed with own code and compared with sensitivity_poststrat.csv."""
import numpy as np
import pandas as pd
from test_validation_rebuild import Q, aligned, built, own_matrices  # noqa: F401


def test_poststrat(built):  # noqa: F811
    Hall, top10, new, car, labelled, groups = own_matrices(built)
    tagged = built["lab"]["tagged"].to_numpy()
    glist = sorted(set(groups[labelled]))
    ps = pd.read_csv(Q / "sensitivity_poststrat.csv")
    Hw = Hall.copy()
    for t in range(7):
        for mk in (tagged, ~tagged):
            ins = Hall[mk, t].sum()
            lab_h = Hall[mk & labelled, t].sum()
            Hw[mk, t] = Hall[mk, t] * ins / lab_h
    Hw = Hw[labelled]
    g = groups[labelled]
    S = np.array([[100 * Hw[g == gg, t].sum() / Hw[:, t].sum() for t in range(7)] for gg in glist])
    A = aligned(S, 0, 1.0)
    worst = 0
    for _, r in ps.iterrows():
        gi = glist.index(r.genre)
        up, dn = A[gi].min(), (-A[gi]).min()
        print(f"POSTSTRAT {r.genre:24s} up mine={up:.4f} analyst={r.check1_margin_up:.4f}; down mine={dn:.4f} analyst={r.check1_margin_down:.4f}")
        worst = max(worst, abs(up - r.check1_margin_up), abs(dn - r.check1_margin_down))
    print("POSTSTRAT worst abs diff:", worst)
    assert worst < 1e-6
