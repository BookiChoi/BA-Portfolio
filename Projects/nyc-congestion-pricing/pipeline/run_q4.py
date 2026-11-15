"""Q4: share of trips touching the Congestion Relief Zone list (plan section 6)."""
import json

import numpy as np
import pandas as pd

from . import analyze as A, config as C, load as L, visualize as V

YEARS = (2023, 2024, 2026)
JAN_SEP = lambda y: [(y, m) for m in range(1, 10)]


def zone_id_check(lk_ids):
    """Plan section 2: IDs outside the lookup per service and year; stop Q4 if any (non-null) exceeds 0.1% of trips."""
    rows = []
    for s in C.SERVICES:
        for y in YEARS:
            pu = A.load_cache(s, "dhp", JAN_SEP(y)).groupby("pu").n.sum()
            do = A.load_cache(s, "do_date", JAN_SEP(y)).groupby("do").n.sum()
            tot = int(pu.sum())
            for kind, ser in (("PU", pu), ("DO", do)):
                bad = ser[~ser.index.isin(lk_ids)]
                rows.append({"service": s, "year": y, "field": kind, "trips": tot, "distinct_ids": len(ser),
                             "ids_not_in_lookup": str(sorted(int(i) for i in bad.index)), "trips_with_such_ids": int(bad.sum()),
                             "share_of_trips": float(bad.sum() / tot),
                             "null_id_trips": int(ser.get(-1, 0))})
    df = pd.DataFrame(rows)
    nonnull = df.trips_with_such_ids - df.null_id_trips
    assert (nonnull / df.trips <= 0.001).all(), "STOP Q4: non-null IDs outside the lookup exceed 0.1% of trips"
    return df


def period_weekly(service, year):
    """Weekly vectors for one period: numerator, denominator, all trips, in-zone (any validity)."""
    f = A.load_cache(service, "flags", JAN_SEP(year))
    f["week"] = A.week_start(f.date)
    f["valid"] = f.vpu & f.vdo
    g = f.assign(num=np.where(f.valid & f.inzone, f.n, 0), den=np.where(f.valid, f.n, 0), inz_all=np.where(f.inzone, f.n, 0))
    wk = g.groupby("week")[["num", "den", "inz_all", "n"]].sum().sort_index()
    mon = g.assign(month=g.date.dt.month).groupby("month")[["num", "den", "inz_all", "n"]].sum()
    return wk, mon


def boot_share(wk, num_col, den_col, Wt):
    num = Wt @ wk[num_col].values
    den = Wt @ wk[den_col].values
    return num / den


def main():
    out = C.OUT / "q4"
    out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 280, "display.max_columns", 40, "display.max_rows", 200)
    lk = L.read_lookup()
    lk_ids = set(lk.LocationID)
    zname = lk.set_index("LocationID").Zone.to_dict()
    zbor = lk.set_index("LocationID").Borough.to_dict()
    crz = set(pd.read_csv(C.OUT / "reference" / "crz_zone_ids.csv").LocationID)
    nbr = pd.read_csv(C.OUT / "reference" / "crz_neighbour_zone_ids.csv")
    ids = np.array(A.valid_zone_ids())

    chk = zone_id_check(lk_ids)
    chk.to_csv(out / "q4_zone_id_check.csv", index=False)
    print("== zone-ID check across years (IDs not in lookup; null = -1) ==")
    print(chk.to_string(index=False))

    rng = np.random.default_rng(C.SEED + 4)
    res_rows, mon_rows, sens_rows = [], [], []
    p_main = {}
    for s in C.SERVICES:
        wk, mon, reps = {}, {}, {}
        for y in YEARS:
            wk[y], mon[y] = period_weekly(s, y)
            Wt = A.boot_weights(len(wk[y]), C.B, rng)   # periods resampled independently (plan)
            reps[y] = boot_share(wk[y], "num", "den", Wt)
            reps[(y, "S4")] = boot_share(wk[y], "inz_all", "n", Wt)
        pt = {y: wk[y].num.sum() / wk[y].den.sum() for y in YEARS}
        pt4 = {y: wk[y].inz_all.sum() / wk[y].n.sum() for y in YEARS}
        for y in YEARS:
            lo, hi = A.pct_ci(reps[y])
            res_rows.append({"service": s, "row_type": "period", "period": str(y), "share": pt[y], "share_lo": lo, "share_hi": hi,
                             "trips_in_month_files": int(wk[y].n.sum()), "valid_denominator": int(wk[y].den.sum()),
                             "in_zone_trips": int(wk[y].num.sum()), "excluded_invalid_id_trips": int(wk[y].n.sum() - wk[y].den.sum()),
                             "excluded_share": float(1 - wk[y].den.sum() / wk[y].n.sum()), "weeks": len(wk[y])})
            for m, r in mon[y].iterrows():
                mon_rows.append({"service": s, "year": y, "month": int(m), "share": r.num / r.den, "valid_denominator": int(r.den),
                                 "in_zone_trips": int(r.num), "excluded_share": float(1 - r.den / r.n)})
        d_main, d_drift = pt[2026] - pt[2024], pt[2024] - pt[2023]
        r_main, r_drift = reps[2026] - reps[2024], reps[2024] - reps[2023]
        margin_pt = abs(d_main) - abs(d_drift)
        margin_rep = np.abs(r_main) - np.abs(r_drift)
        rel_rep = r_main / reps[2024]
        p = A.one_sided_boot_p(r_main, "less")
        p_main[s] = p
        for name, pt_v, rep_v in (("main", d_main, r_main), ("drift", d_drift, r_drift)):
            lo, hi = A.pct_ci(rep_v)
            res_rows.append({"service": s, "row_type": "delta", "period": name, "share": pt_v, "share_lo": lo, "share_hi": hi,
                             "p_one_sided_raw": p if name == "main" else np.nan})
        lo, hi = A.pct_ci(margin_rep)
        res_rows.append({"service": s, "row_type": "margin", "period": "abs(main)-abs(drift)", "share": margin_pt, "share_lo": lo, "share_hi": hi,
                         "decision": "real shift: review guidance" if margin_pt > 0 else "keep current guidance"})
        lo, hi = A.pct_ci(rel_rep)
        res_rows.append({"service": s, "row_type": "relative_change", "period": "main/share2024", "share": d_main / pt[2024], "share_lo": lo, "share_hi": hi})
        # S4: all trips as denominator
        d4m, d4d = pt4[2026] - pt4[2024], pt4[2024] - pt4[2023]
        m4 = abs(d4m) - abs(d4d)
        m4_rep = np.abs(reps[(2026, "S4")] - reps[(2024, "S4")]) - np.abs(reps[(2024, "S4")] - reps[(2023, "S4")])
        lo, hi = A.pct_ci(m4_rep)
        sens_rows.append({"service": s, "share2023_S4": pt4[2023], "share2024_S4": pt4[2024], "share2026_S4": pt4[2026],
                          "delta_main_S4": d4m, "delta_drift_S4": d4d, "margin_S4": m4, "margin_S4_lo": lo, "margin_S4_hi": hi,
                          "decision_S4": "real shift" if m4 > 0 else "keep"})
    res = pd.DataFrame(res_rows)
    # Holm over the 2 service tests of Delta_main < 0
    mains = res[(res.row_type == "delta") & (res.period == "main")]
    hp = A.holm(mains.p_one_sided_raw.values)
    res.loc[mains.index, "p_holm"] = hp
    res.to_csv(out / "q4_share_results.csv", index=False)
    mon_df = pd.DataFrame(mon_rows)
    mon_df.to_csv(out / "q4_monthly_share.csv", index=False)
    sens = pd.DataFrame(sens_rows)
    sens.to_csv(out / "q4_sensitivity_S4.csv", index=False)
    print("\n== Q4 results: shares are fractions; delta/margin rows are fractions (x100 = pp) ==")
    print(res.round(5).to_string(index=False))
    print("\n== monthly shares ==")
    print(mon_df.round(5).to_string(index=False))
    print("\n== S4 sensitivity (all trips as denominator) ==")
    print(sens.round(5).to_string(index=False))

    # ---- fee cross-check (Oct 2025 - Sep 2026 files)
    fee_rows, zone_rows = [], []
    for s in C.SERVICES:
        f = A.load_cache(s, "fee", C.Q123_MONTHS)
        f["week"] = A.week_start(f.date)
        f["pos"] = f.fee_state == 2
        tot = int(f.n.sum())
        fee_pos = int(f[f.pos].n.sum())
        inz = int(f[f.inzone].n.sum())
        both = int(f[f.pos & f.inzone].n.sum())
        null_fee = int(f[f.fee_state == 0].n.sum())
        zero_fee = int(f[f.fee_state == 1].n.sum())
        g = f.assign(pos_n=np.where(f.pos, f.n, 0), inz_n=np.where(f.inzone, f.n, 0), both_n=np.where(f.pos & f.inzone, f.n, 0)).groupby("week")[["pos_n", "inz_n", "both_n"]].sum()
        Wt = A.boot_weights(len(g), C.B, np.random.default_rng(C.SEED + 5))
        i_rep = (Wt @ g.both_n.values) / (Wt @ g.pos_n.values)
        ii_rep = (Wt @ g.both_n.values) / (Wt @ g.inz_n.values)
        i_lo, i_hi = A.pct_ci(i_rep)
        ii_lo, ii_hi = A.pct_ci(ii_rep)
        fee_rows.append({"service": s, "trips": tot, "fee_positive": fee_pos, "fee_zero_or_neg": zero_fee, "fee_null": null_fee,
                         "in_zone_trips": inz, "fee_pos_and_in_zone": both,
                         "i_share_of_fee_trips_with_inzone_end": both / fee_pos, "i_lo": i_lo, "i_hi": i_hi,
                         "ii_share_of_inzone_trips_with_fee": both / inz, "ii_lo": ii_lo, "ii_hi": ii_hi,
                         "flag_i_below_80pct": both / fee_pos < 0.80})
        # zone-level fee share of pickups, Jan-Sep 2026 only
        z = f[f.date.dt.year == 2026].groupby("pu").apply(lambda x: pd.Series({"pickups": x.n.sum(), "pickups_with_fee": x[x.pos].n.sum()}), include_groups=False)
        z["fee_share"] = z.pickups_with_fee / z.pickups
        z = z.reset_index()
        z["service"] = s
        z["zone"] = z.pu.map(zname)
        z["borough"] = z.pu.map(zbor)
        z["in_crz_list"] = z.pu.isin(crz)
        zone_rows.append(z)
    fee = pd.DataFrame(fee_rows)
    fee.to_csv(out / "q4_fee_crosscheck.csv", index=False)
    zf = pd.concat(zone_rows)
    zf.to_csv(out / "q4_fee_share_by_pickup_zone_2026.csv", index=False)
    print("\n== fee cross-check ==")
    print(fee.round(5).T.to_string())
    for s in C.SERVICES:
        d = zf[zf.service == s]
        low = d[d.in_crz_list & (d.fee_share < 0.5)][["pu", "zone", "pickups", "fee_share"]]
        high = d[~d.in_crz_list & (d.fee_share > 0.5) & d.pu.isin(ids)][["pu", "zone", "borough", "pickups", "fee_share"]]
        print(f"\n{s}: CRZ-list zones with fee share of pickups < 50%: {len(low)}")
        print(low.round(4).to_string(index=False))
        print(f"{s}: zones outside the list with fee share > 50%: {len(high)}")
        print(high.round(4).to_string(index=False))

    # ---- supplementary: change in share of pickups and dropoffs outside the list, 2024 -> 2026
    sup_rows = []
    for s in C.SERVICES:
        sh = {}
        for y in (2024, 2026):
            pu = A.load_cache(s, "dhp", JAN_SEP(y)); pu = pu[pu.pu.isin(ids)].groupby("pu").n.sum()
            do = A.load_cache(s, "do_date", JAN_SEP(y)); do = do[do["do"].isin(ids)].groupby("do").n.sum()
            sh[(y, "pickup")] = (pu / pu.sum()).reindex(ids, fill_value=0.0)
            sh[(y, "dropoff")] = (do / do.sum()).reindex(ids, fill_value=0.0)
        for kind in ("pickup", "dropoff"):
            d = pd.DataFrame({"share2024": sh[(2024, kind)], "share2026": sh[(2026, kind)]})
            d["delta_pp"] = (d.share2026 - d.share2024) * 100
            d["relative_change"] = d.share2026 / d.share2024 - 1
            d.index.name = "zone_id"   # the two series carry different index names (pu / do)
            d = d.reset_index()
            d["zone"] = d.zone_id.map(zname)
            d["borough"] = d.zone_id.map(zbor)
            d["in_crz_list"] = d.zone_id.isin(crz)
            d["service"], d["kind"] = s, kind
            sup_rows.append(d)
    sup = pd.concat(sup_rows, ignore_index=True)
    sup.to_csv(out / "q4_supplementary_zone_share_change.csv", index=False)
    outside = sup[~sup.in_crz_list]
    gl = []
    for (s, kind), d in outside.groupby(["service", "kind"]):
        gl.append(d.nlargest(15, "delta_pp").assign(direction="gain"))
        gl.append(d.nsmallest(15, "delta_pp").assign(direction="loss"))
    gains = pd.concat(gl)
    gains.to_csv(out / "q4_supplementary_top15_gains_losses.csv", index=False)
    print("\n== supplementary: 15 largest gains / losses outside the list ==")
    print(gains[["service", "kind", "direction", "zone_id", "zone", "borough", "share2024", "share2026", "delta_pp"]].round(4).to_string(index=False))
    nb = sup[sup.zone_id.isin(nbr.LocationID)]
    nb.to_csv(out / "q4_neighbour_zone_share_change.csv", index=False)
    print("\n== neighbouring zones (geometry-based, plan open item B) ==")
    print(nb[["service", "kind", "zone_id", "zone", "share2024", "share2026", "delta_pp", "relative_change"]].round(5).to_string(index=False))
    print("\nneighbour zones combined share (pickup / dropoff):")
    print(nb.groupby(["service", "kind"])[["share2024", "share2026", "delta_pp"]].sum().round(5).to_string())
    crz_tot = sup[sup.in_crz_list].groupby(["service", "kind"])[["share2024", "share2026", "delta_pp"]].sum()
    print("\nCRZ-list zones combined share (pickup / dropoff, among valid IDs):")
    print(crz_tot.round(5).to_string())

    fig = V.plot_q4_bars(res)
    fig.savefig(out / "q4_share_by_year.png", dpi=130); V.plt.close(fig)
    fig = V.plot_q4_monthly(mon_df)
    fig.savefig(out / "q4_monthly_share.png", dpi=130); V.plt.close(fig)
    fig = V.plot_q4_gains(gains)
    fig.savefig(out / "q4_top15_gains_outside_zone.png", dpi=130); V.plt.close(fig)
    print("\nfigures written to", out)


if __name__ == "__main__":
    main()
