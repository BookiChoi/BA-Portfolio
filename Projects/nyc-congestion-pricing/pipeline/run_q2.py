"""Q2: where airport trips end (plan section 4)."""
import json

import numpy as np
import pandas as pd

from . import analyze as A, config as C, load as L, visualize as V

MIN_TRIPS = 1000   # plan: pairs below this get no decision


def top5_share(R):
    """R: (B, Z) or (Z,) counts -> share of the 5 largest zones. Top 5 is re-selected for every row."""
    R = np.atleast_2d(R).astype(float)
    S = -np.sort(-R, axis=1)[:, :5]
    return S.sum(1) / R.sum(1)


def main():
    out = C.OUT / "q2"
    out.mkdir(parents=True, exist_ok=True)
    ids = np.array(A.valid_zone_ids())
    zi = {z: i for i, z in enumerate(ids)}
    zname = L.read_lookup().set_index("LocationID").Zone.to_dict()
    rng = np.random.default_rng(C.SEED + 2)   # separate stream per question; seed documented in 05

    per = {}
    for s in C.SERVICES:
        dh = A.load_cache(s, "dhp", C.Q123_MONTHS)
        ap = A.load_cache(s, "airport", C.Q123_MONTHS)
        dh = dh[dh.pu.isin(ids)]
        weeks = sorted(set(A.week_start(dh.date)))
        wmap = {w: i for i, w in enumerate(weeks)}
        P = np.zeros((len(weeks), len(ids)))
        np.add.at(P, (A.week_start(dh.date).map(wmap).values, dh.pu.map(zi).values), dh.n.values)
        ap["week"] = A.week_start(ap.date)
        ex = []
        D = {}
        for a in C.AIRPORTS:
            sub = ap[ap.pu == a]
            ok = sub[sub.do.isin(ids)]
            Dm = np.zeros((len(weeks), len(ids)))
            if len(ok):
                np.add.at(Dm, (ok.week.map(wmap).values, ok["do"].map(zi).values), ok.n.values)
            D[a] = Dm
            ex.append({"service": s, "airport_id": a, "airport": C.AIRPORTS[a], "all_airport_pickups": int(sub.n.sum()),
                       "valid_destination_trips": int(ok.n.sum()), "excluded_invalid_destination": int(sub.n.sum() - ok.n.sum()),
                       "same_airport_destination": int(ok[ok["do"] == a].n.sum())})
        per[s] = {"weeks": weeks, "P": P, "D": D, "excl": ex}
        print(f"{s}: weeks {len(weeks)}; overall valid-PU trips {int(P.sum())}")
    assert per["yellow"]["weeks"] == per["fhvhv"]["weeks"]
    nW = len(per["yellow"]["weeks"])
    Wt = A.boot_weights(nW, C.B, rng)   # same weeks drawn for airport and overall within a replicate, and for both services

    rows, top_rows = [], []
    for s in C.SERVICES:
        P = per[s]["P"]
        overall_pt = float(top5_share(P.sum(0))[0])
        overall_rep = top5_share(Wt @ P)
        for a in C.AIRPORTS:
            Dm = per[s]["D"][a]
            n_valid = int(Dm.sum())
            ex = [e for e in per[s]["excl"] if e["airport_id"] == a][0]
            row = {"service": s, "airport_id": a, "airport": C.AIRPORTS[a], **{k: ex[k] for k in
                   ("all_airport_pickups", "valid_destination_trips", "excluded_invalid_destination", "same_airport_destination")},
                   "top5_overall": overall_pt, "top5_overall_lo": A.pct_ci(overall_rep)[0], "top5_overall_hi": A.pct_ci(overall_rep)[1]}
            if n_valid == 0:
                row.update({"top5_airport": np.nan, "status": "too small (no valid trips)"})
                rows.append(row)
                continue
            t5_pt = float(top5_share(Dm.sum(0))[0])
            reps = Wt @ Dm
            # a replicate with zero airport trips (possible for tiny pairs) has no share: mark nan
            tot = reps.sum(1)
            with np.errstate(invalid="ignore", divide="ignore"):
                t5_rep = np.where(tot > 0, top5_share(np.where(tot[:, None] > 0, reps, 1.0)), np.nan)
            delta_rep = (t5_rep - overall_rep) * 100
            ok = ~np.isnan(delta_rep)
            delta_pt = (t5_pt - overall_pt) * 100
            row.update({"top5_airport": t5_pt, "top5_airport_lo": float(np.nanpercentile(t5_rep, 2.5)),
                        "top5_airport_hi": float(np.nanpercentile(t5_rep, 97.5)),
                        "delta_pp": delta_pt, "delta_lo": float(np.nanpercentile(delta_rep, 2.5)), "delta_hi": float(np.nanpercentile(delta_rep, 97.5)),
                        "ratio": t5_pt / overall_pt,
                        "ratio_lo": float(np.nanpercentile(t5_rep / overall_rep, 2.5)), "ratio_hi": float(np.nanpercentile(t5_rep / overall_rep, 97.5)),
                        "p_one_sided_raw": A.one_sided_boot_p(delta_rep[ok], "greater"),
                        "valid_replicates": int(ok.sum()),
                        "status": "too small (<1000 valid trips): descriptive only" if n_valid < MIN_TRIPS else "tested"})
            rows.append(row)
            tot_a = Dm.sum(0)
            rid, rc = A.ranked(tot_a, ids)
            for r in range(10):
                top_rows.append({"service": s, "airport_id": a, "airport": C.AIRPORTS[a], "rank": r + 1, "zone_id": int(rid[r]),
                                 "zone": zname[rid[r]], "trips": int(rc[r]), "share": float(rc[r] / tot_a.sum()),
                                 "cum_share": float(rc[:r + 1].sum() / tot_a.sum())})
    res = pd.DataFrame(rows)
    # Holm over the 6 airport x service comparisons; pairs with no decision (too small) stay in the family count of 6 as planned
    tested = res.status == "tested"
    # why: a too-small pair gets no test and no decision, so its p is blanked; it still counts in the family size (m = 6, as planned)
    res.loc[~tested, "p_one_sided_raw"] = np.nan
    praw = res["p_one_sided_raw"].fillna(1.0).values
    res["p_holm"] = A.holm(praw)
    res.loc[~tested, "p_holm"] = np.nan
    res["decision_point_estimate"] = np.where(tested & (res.delta_pp > 0), "name destinations in guidance",
                                      np.where(tested, "do not name destinations", "no decision (too small)"))
    res["significant_after_holm"] = tested & (res.p_holm < C.ALPHA)
    res.to_csv(out / "q2_airport_top5_vs_overall.csv", index=False)
    pd.DataFrame(top_rows).to_csv(out / "q2_airport_top10_destinations.csv", index=False)
    pd.set_option("display.width", 280, "display.max_columns", 40)
    print("\n== Q2 results (shares are fractions; delta in percentage points) ==")
    print(res.round(4).to_string(index=False))
    tr = pd.DataFrame(top_rows)
    print("\n== top 10 destinations per airport and service ==")
    print(tr.round(4).to_string(index=False))

    fig = V.plot_q2_destinations(tr)
    fig.savefig(out / "q2_airport_top10_destinations.png", dpi=130); V.plt.close(fig)
    fig = V.plot_q2_dots(res)
    fig.savefig(out / "q2_top5_airport_vs_overall.png", dpi=130); V.plt.close(fig)
    print("\nfigures written to", out)


if __name__ == "__main__":
    main()
