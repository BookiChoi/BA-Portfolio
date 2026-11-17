"""Q3: weekday vs weekend shape of the day, night share (plan section 5)."""
import itertools

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from . import analyze as A, config as C, visualize as V

HOLIDAYS = pd.read_csv(C.OUT / "reference" / "holidays_excluded_weekdays.csv", parse_dates=["date"]).date
DOW_MON_THU = [0, 1, 2, 3]


def hourly(service):
    """Date x hour trip counts (all in-month trips, any PU: Q3 needs the pickup datetime only)."""
    d = A.load_cache(service, "dhp", C.Q123_MONTHS)
    h = d.groupby(["date", "hour"]).n.sum().unstack(fill_value=0)
    h = h.reindex(columns=range(24), fill_value=0)
    return h


def day_table(h, night_hours, shifted=False):
    """Per-day total, night trips, share. shifted=True assigns hours 0-4 to the previous calendar day (S3)."""
    dates = h.index
    if not shifted:
        t = pd.DataFrame({"total": h.sum(1), "night": h[list(night_hours)].sum(1)})
    else:
        early = [x for x in night_hours if x < 12]   # 0-4 (or 0-5)
        late = [x for x in night_hours if x >= 12]    # 22, 23
        nxt = h.shift(-1)                              # next calendar day's hours
        # day D (shifted) = hours 5..23 of D plus hours 0-4 of D+1 ; last date has no D+1 -> NaN, dropped
        total = h[[x for x in range(24) if x not in early]].sum(1) + nxt[early].sum(1)
        night = h[late].sum(1) + nxt[early].sum(1)
        t = pd.DataFrame({"total": total, "night": night})
        t = t.iloc[:-1]
    t["share"] = t.night / t.total
    t["dow"] = t.index.weekday
    t["month"] = t.index.strftime("%Y-%m")
    return t


def label_day_types(t, holidays_as_weekdays=False, weekend_nights_fri_sat=False):
    """weekday = Mon-Fri minus holidays (primary), weekend = Sat-Sun. Holidays on Mon-Fri are dropped (None)."""
    t = t.copy()
    if weekend_nights_fri_sat:
        wk = t.dow.isin([4, 5])         # S3 variant reading the plan's stated intent: Fri/Sat nights are weekend nights
        t["dtype"] = np.where(wk, "weekend", "weekday")
        is_hol = t.index.isin(HOLIDAYS) & (not holidays_as_weekdays)
        t.loc[is_hol & ~wk.values, "dtype"] = "holiday"   # a holiday on a Fri/Sat night stays in the weekend group
    else:
        t["dtype"] = np.where(t.dow >= 5, "weekend", "weekday")
        if not holidays_as_weekdays:
            t.loc[t.index.isin(HOLIDAYS) & (t.dow < 5), "dtype"] = "holiday"
    return t


def monthly_decision(t, label):
    """Per month: pooled night shares by day type, gap_m, spread_m (Mon-Thu), Welch test, Hedges g, bootstrap margin CI."""
    rng = np.random.default_rng(C.SEED + 3)
    rows = []
    for m, g in t.groupby("month"):
        wkd, wke = g[g.dtype == "weekday"], g[g.dtype == "weekend"]
        if len(wkd) < 2 or len(wke) < 2:
            continue
        pooled = lambda x: x.night.sum() / x.total.sum()
        gap = pooled(wke) - pooled(wkd)
        dows = {d: g[(g.dow == d) & (g.dtype == "weekday")] for d in DOW_MON_THU}
        sh = {d: pooled(x) for d, x in dows.items() if len(x)}
        spread = max(sh.values()) - min(sh.values())
        # Welch on day-level shares (one-sided: weekend > weekday)
        tt = stats.ttest_ind(wke.share, wkd.share, equal_var=False, alternative="greater")
        d_mean = wke.share.mean() - wkd.share.mean()
        v1, v2, n1, n2 = wke.share.var(ddof=1), wkd.share.var(ddof=1), len(wke), len(wkd)
        se = np.sqrt(v1 / n1 + v2 / n2)
        dfw = se ** 4 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
        tcrit = stats.t.ppf(0.975, dfw)
        sp = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
        J = 1 - 3 / (4 * (n1 + n2) - 9)    # Hedges small-sample correction
        g_h = J * d_mean / sp
        # day-level bootstrap inside month x day-of-week cells (keeps day type fixed; spread needs the DOW cells)
        cells = [x[["night", "total"]].values for _, x in g[g.dtype.isin(["weekday", "weekend"])].groupby(["dow", "dtype"])]
        cell_meta = [(k[0], k[1]) for k, _ in g[g.dtype.isin(["weekday", "weekend"])].groupby(["dow", "dtype"])]
        gaps, margins = [], []
        for _ in range(C.B):
            agg = {"weekday": [0.0, 0.0], "weekend": [0.0, 0.0]}
            dsh = {}
            for arr, (dw, dt) in zip(cells, cell_meta):
                s = arr[rng.integers(0, len(arr), len(arr))]
                agg[dt][0] += s[:, 0].sum(); agg[dt][1] += s[:, 1].sum()
                if dt == "weekday" and dw in DOW_MON_THU:
                    dsh[dw] = s[:, 0].sum() / s[:, 1].sum()
            gp = agg["weekend"][0] / agg["weekend"][1] - agg["weekday"][0] / agg["weekday"][1]
            sp_ = max(dsh.values()) - min(dsh.values())
            gaps.append(gp); margins.append(gp - sp_)
        rows.append({"variant": label, "month": m, "n_weekday_days": n2, "n_weekend_days": n1,
                     "night_share_weekday": pooled(wkd), "night_share_weekend": pooled(wke),
                     "gap_pp": gap * 100, "gap_ci_lo_pp": np.percentile(gaps, 2.5) * 100, "gap_ci_hi_pp": np.percentile(gaps, 97.5) * 100,
                     "spread_pp": spread * 100, "margin_pp": (gap - spread) * 100,
                     "margin_ci_lo_pp": np.percentile(margins, 2.5) * 100, "margin_ci_hi_pp": np.percentile(margins, 97.5) * 100,
                     "dayavg_diff_pp": d_mean * 100, "dayavg_ci_lo_pp": (d_mean - tcrit * se) * 100, "dayavg_ci_hi_pp": (d_mean + tcrit * se) * 100,
                     "welch_t": tt.statistic, "welch_df": dfw, "p_raw": tt.pvalue, "hedges_g": g_h,
                     "gap_gt0": gap > 0, "gap_gt_spread": gap > spread})
    return pd.DataFrame(rows)


def pooled_regression(t):
    """Day-level night share ~ weekend + month fixed effects, HC3 (one regression per service, not in the family)."""
    d = t[t.dtype.isin(["weekday", "weekend"])].copy()
    X = pd.get_dummies(d.month, drop_first=True, dtype=float)
    X["weekend"] = (d.dtype == "weekend").astype(float)
    X = sm.add_constant(X)
    r = sm.OLS(d.share.values, X.values.astype(float)).fit(cov_type="HC3")
    k = list(X.columns).index("weekend")
    ci = r.conf_int()[k]
    return {"coef_pp": r.params[k] * 100, "ci_lo_pp": ci[0] * 100, "ci_hi_pp": ci[1] * 100, "p_two_sided": r.pvalues[k], "n_days": len(d)}


def main():
    out = C.OUT / "q3"
    out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 280, "display.max_columns", 40, "display.max_rows", 200)
    dec_rows, reg_rows, hour_rows, sens_rows, day_rows = [], [], [], [], []
    for s in C.SERVICES:
        h = hourly(s)
        print(f"{s}: days {len(h)} ({h.index.min().date()} .. {h.index.max().date()}), trips {int(h.values.sum())}, zero-trip days {(h.sum(1) == 0).sum()}")
        base = label_day_types(day_table(h, C.NIGHT_HOURS))
        print(f"  day types: {base.dtype.value_counts().to_dict()}")
        dd = monthly_decision(base, "primary")
        dd["service"] = s
        dec_rows.append(dd)
        reg = pooled_regression(base); reg.update({"service": s, "variant": "primary"}); reg_rows.append(reg)
        day_rows.append(base.assign(service=s, variant="primary").reset_index().rename(columns={"index": "date"}))
        # sensitivities
        for lab, tbl in {
            "S1_holidays_as_ordinary": label_day_types(day_table(h, C.NIGHT_HOURS), holidays_as_weekdays=True),
            "S2_hour5_in_night": label_day_types(day_table(h, C.NIGHT_HOURS_S2)),
            "S3_literal_prev_day_Mon-Fri_vs_Sat-Sun": label_day_types(day_table(h, C.NIGHT_HOURS, shifted=True)),
            "S3_intent_Fri-Sat_nights_weekend": label_day_types(day_table(h, C.NIGHT_HOURS, shifted=True), weekend_nights_fri_sat=True),
        }.items():
            x = monthly_decision(tbl, lab)
            x["service"] = s
            sens_rows.append(x)
            rg = pooled_regression(tbl); rg.update({"service": s, "variant": lab}); reg_rows.append(rg)
        # hourly profile: mean trips per hour of day by day type (primary), 95% CI across days (t interval)
        dt = base.dtype
        for typ in ("weekday", "weekend"):
            days = h[dt.reindex(h.index).eq(typ).values]
            norm = days.div(days.sum(1), axis=0)
            for hr in range(24):
                for kind, ser in (("trips_per_day", days[hr]), ("share_of_day", norm[hr])):
                    m_, se_ = ser.mean(), ser.std(ddof=1) / np.sqrt(len(ser))
                    tc = stats.t.ppf(0.975, len(ser) - 1)
                    hour_rows.append({"service": s, "day_type": typ, "hour": hr, "metric": kind, "mean": m_, "lo": m_ - tc * se_, "hi": m_ + tc * se_, "n_days": len(ser)})
    dec = pd.concat(dec_rows, ignore_index=True)
    # Holm over 24 = 12 months x 2 services (primary variant only)
    dec["p_holm"] = np.nan
    dec["p_one_sided_welch"] = dec.p_raw
    dec["p_holm"] = A.holm(dec.p_raw.values)
    dec["sig_holm"] = dec.p_holm < C.ALPHA
    dec.to_csv(out / "q3_monthly_decision_primary.csv", index=False)
    sens = pd.concat(sens_rows, ignore_index=True)
    sens.to_csv(out / "q3_monthly_sensitivities.csv", index=False)
    reg = pd.DataFrame(reg_rows)
    reg.to_csv(out / "q3_pooled_regression.csv", index=False)
    hr = pd.DataFrame(hour_rows)
    hr.to_csv(out / "q3_hourly_profile.csv", index=False)
    pd.concat(day_rows).to_csv(out / "q3_day_level_night_share_primary.csv", index=False)

    cols = ["service", "month", "n_weekday_days", "n_weekend_days", "night_share_weekday", "night_share_weekend", "gap_pp",
            "gap_ci_lo_pp", "gap_ci_hi_pp", "spread_pp", "margin_pp", "margin_ci_lo_pp", "margin_ci_hi_pp", "dayavg_diff_pp",
            "dayavg_ci_lo_pp", "dayavg_ci_hi_pp", "hedges_g", "p_raw", "p_holm", "gap_gt0", "gap_gt_spread"]
    print("\n== PRIMARY: monthly decision table (pp = percentage points) ==")
    print(dec[cols].round(3).to_string(index=False))
    print("\n== Decision rule (gap_m > 0 and gap_m > spread_m in all 12 months) per service ==")
    for s, g in dec.groupby("service"):
        ok = bool((g.gap_gt0 & g.gap_gt_spread).all())
        print(s, "months passing:", int((g.gap_gt0 & g.gap_gt_spread).sum()), "of", len(g), "->", "SEPARATE night-hour guidance" if ok else "ONE version")
        print("   months where margin CI includes 0:", g.loc[(g.margin_ci_lo_pp <= 0) & (g.margin_ci_hi_pp >= 0), "month"].tolist())
    print("\n== pooled regression (weekend coefficient, pp, HC3) ==")
    print(reg.round(4).to_string(index=False))
    print("\n== sensitivities: months passing the decision rule ==")
    for (s, v), g in sens.groupby(["service", "variant"]):
        ok = bool((g.gap_gt0 & g.gap_gt_spread).all())
        print(f"{s:7s} {v:42s} months gap>0: {int(g.gap_gt0.sum()):2d}/{len(g)}  gap>spread: {int(g.gap_gt_spread.sum()):2d}/{len(g)}  mean gap pp {g.gap_pp.mean():.3f}  rule passes all months: {ok}")
    print("\n== sensitivity monthly detail ==")
    print(sens[["service", "variant", "month", "gap_pp", "spread_pp", "margin_pp", "gap_gt0", "gap_gt_spread"]].round(3).to_string(index=False))

    fig = V.plot_q3_hourly(hr)
    fig.savefig(out / "q3_hourly_profile.png", dpi=130); V.plt.close(fig)
    fig = V.plot_q3_monthly(dec)
    fig.savefig(out / "q3_monthly_night_share.png", dpi=130); V.plt.close(fig)
    print("\nfigures written to", out)


if __name__ == "__main__":
    main()
