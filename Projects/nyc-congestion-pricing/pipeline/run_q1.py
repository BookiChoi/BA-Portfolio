"""Q1: pickup zones by part of the day, and concentration (plan section 3)."""
import json

import numpy as np
import pandas as pd

from . import analyze as A, config as C, load as L, visualize as V

DPS = ["all"] + list(C.DAYPARTS)   # index 0 = all hours
HOUR2DP = {h: k for k, (dp, hrs) in enumerate(C.DAYPARTS.items(), start=1) for h in hrs}


def build_tensors(service, ids):
    """Return week x daypart x zone and month x daypart x zone count arrays plus bookkeeping."""
    d = A.load_cache(service, "dhp", C.Q123_MONTHS)
    n_in = int(d.n.sum())
    valid = d.pu.isin(ids)
    excl_month = d[~valid].assign(mon=lambda x: x.date.dt.strftime("%Y-%m")).groupby("mon").n.sum()
    tot_month = d.assign(mon=d.date.dt.strftime("%Y-%m")).groupby("mon").n.sum()
    excl = pd.DataFrame({"trips_in_month_files": tot_month, "excluded_invalid_pu": excl_month}).fillna(0).astype(int)
    excl["excluded_share"] = excl.excluded_invalid_pu / excl.trips_in_month_files
    excl["service"] = service
    d = d[valid].copy()
    d["dpi"] = d.hour.map(HOUR2DP)
    d["week"] = A.week_start(d.date)
    d["mon"] = d.date.dt.strftime("%Y-%m")
    weeks = sorted(d.week.unique())
    months = sorted(d.mon.unique())
    zi = {z: i for i, z in enumerate(ids)}
    wi = d.week.map({w: i for i, w in enumerate(weeks)}).values
    mi = d.mon.map({m: i for i, m in enumerate(months)}).values
    zz = d.pu.map(zi).values
    X = np.zeros((len(weeks), 6, len(ids)))
    Mo = np.zeros((len(months), 6, len(ids)))
    np.add.at(X, (wi, d.dpi.values, zz), d.n.values)
    np.add.at(Mo, (mi, d.dpi.values, zz), d.n.values)
    X[:, 0, :] = X[:, 1:, :].sum(1)
    Mo[:, 0, :] = Mo[:, 1:, :].sum(1)
    return X, Mo, weeks, months, excl, n_in


def main():
    out = C.OUT / "q1"
    out.mkdir(parents=True, exist_ok=True)
    ids = np.array(A.valid_zone_ids())
    lk = L.read_lookup().set_index("LocationID")
    zname = lk.Zone.to_dict()
    zbor = lk.Borough.to_dict()
    rng = np.random.default_rng(C.SEED)

    T, Mo, WK, MN, EXCL = {}, {}, {}, {}, []
    X = {}
    for s in C.SERVICES:
        X[s], Mo[s], WK[s], MN[s], ex, n_in = build_tensors(s, ids)
        T[s] = X[s].sum(0)
        assert np.allclose(T[s], Mo[s].sum(0)), "week and month tensors disagree"
        EXCL.append(ex.reset_index().rename(columns={"mon": "month"}))
        print(f"{s}: in-month trips (Oct25-Sep26) {n_in}, valid-PU trips {int(T[s][0].sum())}, "
              f"excluded {n_in - int(T[s][0].sum())} ({(n_in - T[s][0].sum()) / n_in:.4%}); weeks {len(WK[s])}, months {len(MN[s])}")
    assert WK["yellow"] == WK["fhvhv"], "services must share the same week index for paired resampling"
    pd.concat(EXCL).to_csv(out / "q1_exclusions_by_month.csv", index=False)

    # ---- point estimates and bootstrap (paired weeks)
    Wt = A.boot_weights(len(WK["yellow"]), C.B, rng)
    conc, boots = {}, {}
    rows = []
    for s in C.SERVICES:
        pt = A.concentration(T[s])
        R = np.einsum("bw,wdz->bdz", Wt, X[s])
        bt = A.concentration(R.reshape(-1, R.shape[2]))
        boots[s] = {k: v.reshape(C.B, 6) for k, v in bt.items()}
        for k, dp in enumerate(DPS):
            row = {"service": s, "daypart": dp, "valid_trips": int(T[s][k].sum())}
            for key in ("n50", "n80", "top5", "active"):
                lo, hi = A.pct_ci(boots[s][key][:, k])
                row.update({key: float(pt[key][k]), f"{key}_lo": lo, f"{key}_hi": hi})
            rows.append(row)
        conc[s] = {"n50": pt["n50"][0], "n80": pt["n80"][0]}
    cdf = pd.DataFrame(rows)
    cdf.to_csv(out / "q1_concentration.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print("\n== concentration (point estimates with 95% week-block bootstrap CI) ==")
    print(cdf.round(4).to_string(index=False))

    # ---- hypothesis (b): n80(HVFHV) > n80(yellow)
    hb = {}
    for k, dp in enumerate(DPS):
        dif = boots["fhvhv"]["n80"][:, k] - boots["yellow"]["n80"][:, k]
        ratio = boots["fhvhv"]["n80"][:, k] / boots["yellow"]["n80"][:, k]
        pt_d = float(A.concentration(T["fhvhv"])["n80"][k] - A.concentration(T["yellow"])["n80"][k])
        pt_r = float(A.concentration(T["fhvhv"])["n80"][k] / A.concentration(T["yellow"])["n80"][k])
        hb[dp] = {"d_point": pt_d, "d_ci": A.pct_ci(dif), "ratio_point": pt_r, "ratio_ci": A.pct_ci(ratio),
                  "p_one_sided": A.one_sided_boot_p(dif, "greater") if dp == "all" else None,
                  "role": "confirmatory (alpha 0.05, single test, no correction)" if dp == "all" else "descriptive"}
    (out / "q1_hypothesis_b.json").write_text(json.dumps(hb, indent=2))
    print("\n== hypothesis (b): n80(HVFHV) - n80(yellow) ==")
    print(json.dumps(hb, indent=2))

    # ---- hypothesis (a): airports in top 5 (whole period, all hours), and months in monthly top 5
    ap_rows = []
    for s in C.SERVICES:
        rid, rc = A.ranked(T[s][0], ids)
        print(f"\n{s} top 5 pickup zones (all hours):", [(int(z), zname[z], int(c)) for z, c in zip(rid[:5], rc[:5])])
        for a in C.AIRPORTS:
            rank = int(np.where(rid == a)[0][0] + 1)
            in_top5_months = 0
            for m in range(len(MN[s])):
                r2, _ = A.ranked(Mo[s][m, 0], ids)
                in_top5_months += int(a in r2[:5])
            ap_rows.append({"service": s, "airport_id": a, "airport": C.AIRPORTS[a], "rank_whole_period": rank,
                            "in_top5_whole_period": rank <= 5, "months_in_monthly_top5": in_top5_months,
                            "n_months": len(MN[s]), "trips": int(T[s][0][list(ids).index(a)])})
    apdf = pd.DataFrame(ap_rows)
    apdf.to_csv(out / "q1_airport_rank_check.csv", index=False)
    print("\n== hypothesis (a): airport rank check ==")
    print(apdf.to_string(index=False))

    # ---- top 10 per day-part, cumulative curves
    top_rows, curves, curve_rows = [], {}, []
    for s in C.SERVICES:
        for k, dp in enumerate(DPS):
            rid, rc = A.ranked(T[s][k], ids)
            for r in range(10):
                top_rows.append({"service": s, "daypart": dp, "rank": r + 1, "zone_id": int(rid[r]), "zone": zname[rid[r]],
                                 "borough": zbor[rid[r]], "trips": int(rc[r]), "share": float(rc[r] / T[s][k].sum()),
                                 "is_airport": int(rid[r]) in C.AIRPORTS})
        rid, rc = A.ranked(T[s][0], ids)
        cum = np.cumsum(rc) / rc.sum()
        curves[s] = {"rank": np.arange(1, len(ids) + 1), "cum_share": cum}
        curve_rows += [{"service": s, "rank": int(i + 1), "zone_id": int(rid[i]), "cum_share": float(cum[i])} for i in range(len(ids))]
    top10 = pd.DataFrame(top_rows)
    top10.to_csv(out / "q1_top10_by_daypart.csv", index=False)
    pd.DataFrame(curve_rows).to_csv(out / "q1_cumulative_share.csv", index=False)
    print("\n== top 10 pickup zones, all hours ==")
    print(top10[top10.daypart == "all"][["service", "rank", "zone_id", "zone", "trips", "share"]].round(4).to_string(index=False))

    # ---- guidance lists, standing/seasonal, Jaccard
    glist, mem, jac = [], [], []
    for s in C.SERVICES:
        for k, dp in enumerate(DPS):
            frac = 0.5
            full = A.cover_list(T[s][k], ids, frac)
            if len(full) > 30:
                frac = 0.4
                full = A.cover_list(T[s][k], ids, frac)
            monthly = [A.cover_list(Mo[s][m, k], ids, frac) for m in range(len(MN[s]))]
            for m, lst in enumerate(monthly):
                jac.append({"service": s, "daypart": dp, "month": MN[s][m], "frac": frac, "list_len": len(lst),
                            "jaccard_vs_full": len(set(lst) & set(full)) / len(set(lst) | set(full))})
            union = set(full).union(*[set(x) for x in monthly])
            for z in sorted(union):
                for m, lst in enumerate(monthly):
                    mem.append({"service": s, "daypart": dp, "zone_id": int(z), "zone": zname[z], "month": MN[s][m],
                                "in_list": int(z in lst)})
            for z in full:
                nm = sum(z in lst for lst in monthly)
                glist.append({"service": s, "daypart": dp, "coverage_frac": frac, "list_len": len(full), "zone_id": int(z),
                              "zone": zname[z], "months_in_list": nm, "n_months": len(monthly),
                              "status": "standing" if nm == len(monthly) else "seasonal"})
    gl = pd.DataFrame(glist)
    mem = pd.DataFrame(mem)
    jc = pd.DataFrame(jac)
    gl.to_csv(out / "q1_guidance_lists.csv", index=False)
    mem.to_csv(out / "q1_monthly_membership.csv", index=False)
    jc.to_csv(out / "q1_monthly_jaccard.csv", index=False)
    print("\n== guidance lists: size, coverage fraction, standing vs seasonal ==")
    print(gl.groupby(["service", "daypart"]).agg(frac=("coverage_frac", "first"), list_len=("list_len", "first"),
                                                 standing=("status", lambda x: (x == "standing").sum()),
                                                 seasonal=("status", lambda x: (x == "seasonal").sum())).to_string())
    print("\nJaccard of monthly lists vs full-period list (min / mean / max):")
    print(jc.groupby(["service", "daypart"]).jaccard_vs_full.agg(["min", "mean", "max"]).round(3).to_string())
    print("\n== guidance list members (all hours) ==")
    print(gl[gl.daypart == "all"][["service", "zone_id", "zone", "months_in_list", "status"]].to_string(index=False))

    # ---- figures
    fig = V.plot_q1_top10(top10, DPS[1:])
    fig.savefig(out / "q1_top10_by_daypart.png", dpi=130); V.plt.close(fig)
    fig = V.plot_q1_cumulative(curves, conc)
    fig.savefig(out / "q1_cumulative_share.png", dpi=130); V.plt.close(fig)
    for s in C.SERVICES:
        fig = V.plot_q1_standing(mem[mem.service == s], s, DPS)
        fig.savefig(out / f"q1_standing_seasonal_{s}.png", dpi=130); V.plt.close(fig)
    print("\nfigures written to", out)


if __name__ == "__main__":
    main()
