"""Validator: independent recomputation of the analyst numbers (reads validation_cache/agg.pkl built by validation_aggregate.py with DuckDB).
Own bootstrap code and own seeds (analyst: 42-47; validator: 1001+). Writes validation_checks.csv and prints a log."""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

ROOT = Path("/Users/booki/Desktop/BA-Portfolio/Projects/nyc-congestion-pricing")
LOG = ROOT / "workflow/logs"
OUTS = ROOT / "outputs"
res = pickle.load(open(LOG / "validation_cache/agg.pkl", "rb"))
ids = pickle.load(open(LOG / "validation_cache/ids.pkl", "rb"))
VALID = np.array(ids["valid"]); CRZ = set(ids["crz"])
ZI = {z: i for i, z in enumerate(VALID)}
B = 2000
SV = ("yellow", "fhvhv")
Q123 = [(2025, 10), (2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 10)]
JS = lambda y: [(y, m) for m in range(1, 10)]
lk = pd.read_csv(ROOT / "data/taxi_zone_lookup.csv")
ZN = lk.set_index("LocationID").Zone.to_dict()
ZB = lk.set_index("LocationID").Borough.to_dict()
CHK = []


def chk(group, name, a, m, tol, method, note="", kind="abs"):
    """Record a check. kind abs: |a-m|<=tol. For text/bool equality pass tol=None."""
    if tol is None:
        ok = (a == m)
    else:
        ok = bool(abs(float(a) - float(m)) <= tol)
    CHK.append({"group": group, "number": name, "analyst": a, "validator": m, "method": method, "tol": tol, "pass": bool(ok), "note": note})
    return ok


def cat(svc, kind, months):
    fr = []
    for ym in months:
        d = res[(svc, ym[0], ym[1])][kind].copy(); d["ym"] = f"{ym[0]}-{ym[1]:02d}"; fr.append(d)
    d = pd.concat(fr, ignore_index=True)
    if "date" in d: d["date"] = pd.to_datetime(d["date"])
    return d


def week_of(s): return s - pd.to_timedelta(s.dt.weekday, unit="D")


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1, run)
    return adj


def conc(M):
    """M rows = count vectors. returns n50,n80,top5,active"""
    M = np.atleast_2d(M).astype(float); S = -np.sort(-M, 1); cum = np.cumsum(S, 1) / M.sum(1, keepdims=True)
    n50 = np.array([np.searchsorted(c, 0.5, "left") + 1 for c in cum]); n80 = np.array([np.searchsorted(c, 0.8, "left") + 1 for c in cum])
    return n50, n80, cum[:, 4], (M > 0).mean(1)


def pctci(x): return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def bweights(nw, rng):
    idx = rng.integers(0, nw, (B, nw)); W = np.zeros((B, nw))
    for b in range(B): W[b] = np.bincount(idx[b], minlength=nw)
    return W


# ============ 0. DATA CHECKS ============
man = json.load(open(ROOT / "data_manifest.json"))["datasets"]
mrc = {d["name"]: d["row_count"] for d in man}
fq = pd.read_csv(OUTS / "reference/file_quality_counts.csv")
n_ok = 0; mism = []
tot = {"yellow": dict(total=0, in_month=0, inv_pu=0, inv_do=0, null_pickup=0, null_pu=0, null_do=0, dup_key=0, oom=0),
       "fhvhv": dict(total=0, in_month=0, inv_pu=0, inv_do=0, null_pickup=0, null_pu=0, null_do=0, dup_key=0, oom=0)}
for (svc, y, m), r in res.items():
    nm = f"{svc}_tripdata_{y}-{m:02d}.parquet"
    if mrc[nm] == r["total"]: n_ok += 1
    else: mism.append(nm)
    a = fq[(fq.service == svc) & (fq.year == y) & (fq.month == m)].iloc[0]
    for k_a, k_m in (("rows_total", "total"), ("null_pickup", "null_pickup"), ("rows_in_month", "in_month"), ("null_pu", "null_pu"), ("null_do", "null_do"), ("invalid_pu", "inv_pu"), ("invalid_do", "inv_do")):
        if int(a[k_a]) != int(r[k_m]): mism.append(f"{nm}:{k_a} {a[k_a]} vs {r[k_m]}")
    t = tot[svc]
    for k in ("total", "in_month", "inv_pu", "inv_do", "null_pickup", "null_pu", "null_do", "dup_key"): t[k] += r[k]
    t["oom"] += r["total"] - r["null_pickup"] - r["in_month"]
chk("0 data", "60 files: row_count vs data_manifest.json", 60, n_ok, 0, "DuckDB count(*) vs manifest")
chk("0 data", "60 files: analyst file_quality_counts.csv vs validator (total, null, in-month, invalid PU/DO)", 0, len(mism), 0, "DuckDB SQL vs pyarrow", note=str(mism[:5]))
chk("0 data", "HVFHV invalid-DO trips (all 60 files... 30 HVFHV)", 25822247, tot["fhvhv"]["inv_do"], 0, "DuckDB")
chk("0 data", "yellow invalid-DO trips", 980546, tot["yellow"]["inv_do"], 0, "DuckDB")
chk("0 data", "HVFHV invalid-PU trips", 28319, tot["fhvhv"]["inv_pu"], 0, "DuckDB")
chk("0 data", "yellow invalid-PU trips", 502214, tot["yellow"]["inv_pu"], 0, "DuckDB")
chk("0 data", "HVFHV total trips (30 files)", 604313696, tot["fhvhv"]["total"], 0, "DuckDB")
chk("0 data", "yellow total trips (30 files)", 104587416, tot["yellow"]["total"], 0, "DuckDB")
print("DATA CHECKS totals:", json.dumps(tot))
for s in SV:
    t = tot[s]
    print(f"{s}: null pickup {t['null_pickup']}, null PU {t['null_pu']}, null DO {t['null_do']}, out-of-month {t['oom']} ({t['oom']/t['total']:.6%}), "
          f"invalid PU {t['inv_pu']/t['in_month']:.4%}, invalid DO {t['inv_do']/t['in_month']:.4%}, exact key duplicates (pickup,dropoff,PU,DO) {t['dup_key']} ({t['dup_key']/t['total']:.4%})")
dup_by_year = {}
for (svc, y, m), r in res.items():
    dup_by_year.setdefault((svc, y), [0, 0]); dup_by_year[(svc, y)][0] += r["dup_key"]; dup_by_year[(svc, y)][1] += r["total"]
print("dup key share by service-year:", {k: round(v[0] / v[1], 5) for k, v in dup_by_year.items()})
# row-count range check
for s in SV:
    c = pd.Series({k[1:]: v["total"] for k, v in res.items() if k[0] == s}); med = c.median()
    print(s, "monthly rows min/max", c.min(), c.max(), "max |dev from median|", round(float((c / med - 1).abs().max()), 3))
# per-month flag: sums of the analyst's q1 exclusion table (yellow/hvfhv in-month Oct25-Sep26)

# ============ Q1 ============
print("\n==== Q1 ====")
T, WKM, MOM, WEEKS, MONTHS = {}, {}, {}, None, None
HOUR2DP = {}
for k, (dp, hrs) in enumerate({"overnight": range(0, 6), "morning": range(6, 10), "midday": range(10, 16), "evening": range(16, 20), "night": range(20, 24)}.items(), start=1):
    for h in hrs: HOUR2DP[h] = k
DPN = ["all", "overnight", "morning", "midday", "evening", "night"]
EXC = {}
for s in SV:
    d = cat(s, "dhp", Q123)
    EXC[s] = (int(d.n.sum()), int(d[~d.pu.isin(VALID)].n.sum()))
    d = d[d.pu.isin(VALID)].copy()
    d["dp"] = d.hr.map(HOUR2DP); d["wk"] = week_of(d.date)
    WEEKS = sorted(d.wk.unique()); MONTHS = sorted(d.ym.unique())
    wi = d.wk.map({w: i for i, w in enumerate(WEEKS)}).values; mi = d.ym.map({m: i for i, m in enumerate(MONTHS)}).values; zi = d.pu.map(ZI).values
    X = np.zeros((len(WEEKS), 6, len(VALID))); Mo = np.zeros((len(MONTHS), 6, len(VALID)))
    np.add.at(X, (wi, d.dp.values, zi), d.n.values); np.add.at(Mo, (mi, d.dp.values, zi), d.n.values)
    X[:, 0] = X[:, 1:].sum(1); Mo[:, 0] = Mo[:, 1:].sum(1)
    WKM[s] = X; MOM[s] = Mo; T[s] = X.sum(0)
print("weeks", len(WEEKS))
chk("Q1", "yellow in-month trips Oct25-Sep26", 46494334, EXC["yellow"][0], 0, "DuckDB")
chk("Q1", "HVFHV in-month trips Oct25-Sep26", 253409771, EXC["fhvhv"][0], 0, "DuckDB")
chk("Q1", "yellow excluded invalid PU (79,145)", 79145, EXC["yellow"][1], 0, "DuckDB")
chk("Q1", "HVFHV excluded invalid PU (12,835)", 12835, EXC["fhvhv"][1], 0, "DuckDB")
qc = pd.read_csv(OUTS / "q1/q1_concentration.csv")
rng = np.random.default_rng(1001)
Wt = bweights(len(WEEKS), rng)
BOOT = {}
for s in SV:
    for k, dp in enumerate(DPN):
        BOOT[(s, dp)] = conc(Wt @ WKM[s][:, k, :])
for s in SV:
    for k, dp in enumerate(DPN):
        a = qc[(qc.service == s) & (qc.daypart == dp)].iloc[0]
        n50, n80, t5, act = conc(T[s][k])
        g = "Q1" if dp == "all" else "Q1 daypart"
        bn50, bn80, bt5, bact = BOOT[(s, dp)]
        chk(g, f"{s} {dp} valid trips", a.valid_trips, T[s][k].sum(), 0, "numpy vs analyst")
        chk(g, f"{s} {dp} n50", a.n50, n50[0], 0, "sorted cumsum")
        chk(g, f"{s} {dp} n80", a.n80, n80[0], 0, "sorted cumsum")
        chk(g, f"{s} {dp} top5 share", a.top5, t5[0], 1e-9, "sorted cumsum")
        chk(g, f"{s} {dp} active zone share", a.active, act[0], 1e-9, "count>0 / 263")
        lo, hi = pctci(bt5)
        chk(g, f"{s} {dp} top5 CI lo", a.top5_lo, lo, 0.0015, "own week bootstrap, seed 1001, B=2000", "abs tol 0.15pp")
        chk(g, f"{s} {dp} top5 CI hi", a.top5_hi, hi, 0.0015, "own week bootstrap")
        lo, hi = pctci(bn80)
        chk(g, f"{s} {dp} n80 CI lo", a.n80_lo, lo, 1, "own week bootstrap", "tol 1 zone (integer statistic)")
        chk(g, f"{s} {dp} n80 CI hi", a.n80_hi, hi, 1, "own week bootstrap", "tol 1 zone")
        lo, hi = pctci(bn50)
        chk(g, f"{s} {dp} n50 CI lo", a.n50_lo, lo, 1, "own week bootstrap", "tol 1 zone")
        chk(g, f"{s} {dp} n50 CI hi", a.n50_hi, hi, 1, "own week bootstrap", "tol 1 zone")
hb = json.load(open(OUTS / "q1/q1_hypothesis_b.json"))
dpt = BOOT[("fhvhv", "all")][1] - BOOT[("yellow", "all")][1]
rat = BOOT[("fhvhv", "all")][1] / BOOT[("yellow", "all")][1]
n80y, n80f = conc(T["yellow"][0])[1][0], conc(T["fhvhv"][0])[1][0]
chk("Q1", "H(b) d = n80 HVFHV - yellow", hb["all"]["d_point"], n80f - n80y, 0, "recomputed")
chk("Q1", "H(b) ratio", hb["all"]["ratio_point"], n80f / n80y, 1e-9, "recomputed")
lo, hi = pctci(dpt)
chk("Q1", "H(b) d CI lo", hb["all"]["d_ci"][0], lo, 1, "own paired week bootstrap")
chk("Q1", "H(b) d CI hi", hb["all"]["d_ci"][1], hi, 1, "own paired week bootstrap")
pb = (1 + (dpt <= 0).sum()) / (B + 1)
chk("Q1", "H(b) one-sided p", hb["all"]["p_one_sided"], pb, 0.0005, "own bootstrap (+1 rule)", "both at floor 1/2001")
for dp in DPN[1:]:
    dd = conc(T["fhvhv"][DPN.index(dp)])[1][0] - conc(T["yellow"][DPN.index(dp)])[1][0]
    chk("Q1 daypart", f"d n80 {dp}", hb[dp]["d_point"], dd, 0, "recomputed")
# airport ranks
ar = pd.read_csv(OUTS / "q1/q1_airport_rank_check.csv")
def rank_of(v, zid):
    o = np.lexsort((VALID, -v)); return int(np.where(VALID[o] == zid)[0][0]) + 1
for s in SV:
    for _, r in ar[ar.service == s].iterrows():
        k = DPN.index("all")
        chk("Q1 airports", f"{s} {r.airport} rank whole period", r.rank_whole_period, rank_of(T[s][0], r.airport_id), 0, "lexsort")
        mt = sum(1 for mi_ in range(len(MONTHS)) if rank_of(MOM[s][mi_, 0], r.airport_id) <= 5)
        chk("Q1 airports", f"{s} {r.airport} months in monthly top-5", r.months_in_monthly_top5, mt, 0, "lexsort per month")
        chk("Q1 airports", f"{s} {r.airport} trips", r.trips, T[s][0][ZI[r.airport_id]], 0, "sum")
# guidance lists
gl = pd.read_csv(OUTS / "q1/q1_guidance_lists.csv"); mj = pd.read_csv(OUTS / "q1/q1_monthly_jaccard.csv")
def cover(v, frac):
    o = np.lexsort((VALID, -v)); c = np.cumsum(v[o]) / v.sum(); k = int((c < frac).sum() + 1); return list(VALID[o][:k])
for s in SV:
    for k, dp in enumerate(DPN):
        full = cover(T[s][k], 0.5); frac = 0.5
        if len(full) > 30: frac = 0.4; full = cover(T[s][k], 0.4)
        mem = {z: 0 for z in full}; jac = []
        for mi_ in range(len(MONTHS)):
            lm = cover(MOM[s][mi_, k], frac)
            for z in lm:
                if z in mem: mem[z] += 1
            jac.append(len(set(lm) & set(full)) / len(set(lm) | set(full)))
        g = gl[(gl.service == s) & (gl.daypart == dp)]
        stand = sum(1 for z in mem if mem[z] == 12)
        a_stand = int((g.status == "standing").sum())
        gg = "Q1 lists" if dp == "all" else "Q1 lists daypart"
        chk(gg, f"{s} {dp} list length (coverage {frac})", int(g.list_len.iloc[0]), len(full), 0, "recomputed cover list")
        chk(gg, f"{s} {dp} coverage fraction used", float(g.coverage_frac.iloc[0]), frac, 0, "recomputed")
        chk(gg, f"{s} {dp} standing zones", a_stand, stand, 0, "recomputed membership over 12 monthly lists")
        sameset = set(g.zone_id) == set(full)
        chk(gg, f"{s} {dp} list membership identical", True, sameset, None, "set equality")
        j = mj[(mj.service == s) & (mj.daypart == dp)].jaccard_vs_full
        chk(gg, f"{s} {dp} Jaccard min", float(j.min()), min(jac), 1e-9, "recomputed")
        chk(gg, f"{s} {dp} Jaccard mean", float(j.mean()), float(np.mean(jac)), 1e-9, "recomputed")

# ============ Q2 ============
print("\n==== Q2 ====")
q2 = pd.read_csv(OUTS / "q2/q2_airport_top5_vs_overall.csv")
AIRP = {1: "Newark Airport", 132: "JFK Airport", 138: "LaGuardia Airport"}
pvals = []; Q2 = {}
rng2 = np.random.default_rng(1002)
Wq2 = bweights(len(WEEKS), rng2)
wk_index = {w: i for i, w in enumerate(WEEKS)}
oos_rows = []
for s in SV:
    a = cat(s, "airport", Q123); a["wk"] = week_of(a.date); a["wi"] = a.wk.map(wk_index)
    ov_rep = conc(Wt @ WKM[s][:, 0, :] if False else Wq2 @ WKM[s][:, 0, :])[2]
    top5_overall = conc(T[s][0])[2][0]
    for aid, an in AIRP.items():
        x = a[a.pu == aid]
        validd = x[x.dof.isin(VALID)]
        M = np.zeros((len(WEEKS), len(VALID))); np.add.at(M, (validd.wi.values.astype(int), validd.dof.map(ZI).values), validd.n.values)
        v = M.sum(0); nval = v.sum()
        r = q2[(q2.service == s) & (q2.airport_id == aid)].iloc[0]
        chk("Q2", f"{s} {an} all pickups", r.all_airport_pickups, x.n.sum(), 0, "DuckDB")
        chk("Q2", f"{s} {an} valid dest trips", r.valid_destination_trips, nval, 0, "DuckDB")
        chk("Q2", f"{s} {an} excluded invalid dest", r.excluded_invalid_destination, x.n.sum() - nval, 0, "DuckDB")
        chk("Q2", f"{s} {an} same-airport dest", r.same_airport_destination, x[x.dof == aid].n.sum(), 0, "DuckDB")
        if nval < 1000:
            Q2[(s, aid)] = None
            chk("Q2", f"{s} {an} too small (<1000) -> no decision", True, str(r.status).startswith("too small") and "no decision" in str(r.decision_point_estimate).lower(), None, "status/decision text", note=f"{r.status} | {r.decision_point_estimate}"); continue
        t5 = conc(v)[2][0]
        rep_air = conc(Wq2 @ M)[2]
        d = (t5 - top5_overall) * 100; drep = (rep_air - ov_rep) * 100
        chk("Q2", f"{s} {an} top5_airport", r.top5_airport, t5, 1e-9, "sorted cumsum")
        chk("Q2", f"{s} {an} top5_overall", r.top5_overall, top5_overall, 1e-9, "sorted cumsum")
        chk("Q2", f"{s} {an} delta pp", r.delta_pp, d, 1e-7, "recomputed")
        lo, hi = pctci(drep)
        chk("Q2", f"{s} {an} delta CI lo (pp)", r.delta_lo, lo, 0.15, "own bootstrap, top-5 re-selected per replicate, seed 1002", "tol 0.15 pp")
        chk("Q2", f"{s} {an} delta CI hi (pp)", r.delta_hi, hi, 0.15, "own bootstrap")
        chk("Q2", f"{s} {an} ratio", r.ratio, t5 / top5_overall, 1e-9, "recomputed")
        p = (1 + (drep <= 0).sum()) / (B + 1); pvals.append(((s, aid), p))
        chk("Q2", f"{s} {an} decision", r.decision_point_estimate, "name destinations in guidance" if t5 > top5_overall else "do not name destinations", None, "decision rule on point estimate")
        # out-of-sample selection check: choose top5 on odd weeks, measure on even weeks (both airport and overall)
        odd = np.arange(len(WEEKS)) % 2 == 1
        def oos(Mx):
            sel = np.argsort(-Mx[odd].sum(0))[:5]; return Mx[~odd][:, sel].sum() / Mx[~odd].sum()
        oos_rows.append((s, an, oos(M), oos(WKM[s][:, 0, :]), t5, top5_overall))
        Q2[(s, aid)] = (t5, top5_overall)
praw = {k: p for k, p in pvals}
keys = [(s, a) for s in SV for a in AIRP]
pl = [praw.get(k, 1.0) for k in keys]
hp = dict(zip(keys, holm(pl)))
for k, v in praw.items():
    r = q2[(q2.service == k[0]) & (q2.airport_id == k[1])].iloc[0]
    chk("Q2", f"{k[0]} {AIRP[k[1]]} Holm p (family of 6, too-small pair counted as p=1)", r.p_holm, hp[k], 0.0005, "own Holm over 6")
print("Q2 out-of-sample selection check (odd weeks select, even weeks measure): service airport oos_air oos_overall | in-sample air, overall")
for r in oos_rows: print(r[0], r[1], f"{r[2]:.4f} {r[3]:.4f} | {r[4]:.4f} {r[5]:.4f}  decision_flip={(r[2] > r[3]) != (r[4] > r[5])}")
pickle.dump(oos_rows, open(LOG / "validation_cache/q2_oos.pkl", "wb"))
t10 = pd.read_csv(OUTS / "q2/q2_airport_top10_destinations.csv")
for s in SV:
    a = cat(s, "airport", Q123)
    for aid, an in AIRP.items():
        x = a[(a.pu == aid) & a.dof.isin(VALID)]
        if x.n.sum() < 1000: continue
        vc = x.groupby("dof").n.sum(); vc = vc.reindex(sorted(vc.index)); o = np.lexsort((vc.index.values, -vc.values))
        top = vc.index.values[o][:5]
        a_top = t10[(t10.service == s) & (t10.airport_id == aid)].sort_values("rank").zone_id.values[:5]
        chk("Q2", f"{s} {an} top-5 destination IDs", str(list(a_top)), str(list(top)), None, "ranking recomputed", "set/order of IDs")

# ============ Q3 ============
print("\n==== Q3 ====")
HOL = pd.to_datetime(["2025-10-13", "2025-11-11", "2025-11-27", "2025-12-25", "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07"])
hol_a = pd.read_csv(OUTS / "reference/holidays_excluded_weekdays.csv", parse_dates=["date"]).date
chk("Q3", "holiday list equals plan table (11 dates)", True, bool(set(hol_a) == set(HOL)), None, "set equality with plan section 5")
dec = pd.read_csv(OUTS / "q3/q3_monthly_decision_primary.csv"); sens = pd.read_csv(OUTS / "q3/q3_monthly_sensitivities.csv")
reg_a = pd.read_csv(OUTS / "q3/q3_pooled_regression.csv")
NIGHT = {22, 23, 0, 1, 2, 3, 4}; NIGHT2 = NIGHT | {5}
rng3 = np.random.default_rng(1003)


def daytab(s, night, shift=False):
    d = cat(s, "dhp", Q123).groupby(["date", "hr"]).n.sum().reset_index()
    d["night"] = d.hr.isin(night)
    if shift:
        early = d.hr <= 4
        d["adate"] = np.where(early, d.date - pd.Timedelta(days=1), d.date); d["adate"] = pd.to_datetime(d.adate)
        # NB: only hours 0-4 are re-assigned; night definition (22-04) unchanged
    else:
        d["adate"] = d.date
    g = d.groupby("adate").apply(lambda x: pd.Series({"total": x.n.sum(), "nightn": x.n[x.night].sum()}), include_groups=False)
    if shift:  # first assigned date (09-30) and last (09-30, hours 0-4 of Oct 1 2026 not in data) are incomplete
        g = g[(g.index >= "2025-10-01") & (g.index <= "2026-09-29")]
    g["share"] = g.nightn / g.total; g["dow"] = g.index.weekday; g["month"] = g.index.strftime("%Y-%m")
    return g


def label(g, hol_weekday_ordinary=False, fri_sat=False):
    g = g.copy()
    if fri_sat:
        wk = g.dow.isin([4, 5]); g["dt"] = np.where(wk, "weekend", "weekday")
        if not hol_weekday_ordinary: g.loc[g.index.isin(HOL) & ~wk.values, "dt"] = "holiday"
    else:
        g["dt"] = np.where(g.dow >= 5, "weekend", "weekday")
        if not hol_weekday_ordinary: g.loc[g.index.isin(HOL) & (g.dow < 5), "dt"] = "holiday"
    return g


def monthly(g, boot=False):
    out = []
    for m, x in g.groupby("month"):
        wd, we = x[x.dt == "weekday"], x[x.dt == "weekend"]
        pooled = lambda z: z.nightn.sum() / z.total.sum()
        gap = pooled(we) - pooled(wd)
        sp = [pooled(wd[wd.dow == d]) for d in range(4) if (wd.dow == d).any()]
        spread = max(sp) - min(sp)
        t = stats.ttest_ind(we.share, wd.share, equal_var=False, alternative="greater")
        n1, n2 = len(we), len(wd); v1, v2 = we.share.var(ddof=1), wd.share.var(ddof=1)
        sdp = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)); gh = (1 - 3 / (4 * (n1 + n2) - 9)) * (we.share.mean() - wd.share.mean()) / sdp
        mw = stats.mannwhitneyu(we.share, wd.share, alternative="greater").pvalue
        r = dict(month=m, n_wd=n2, n_we=n1, sh_wd=pooled(wd), sh_we=pooled(we), gap=gap * 100, spread=spread * 100, margin=(gap - spread) * 100,
                 t=t.statistic, df=t.df, p=t.pvalue, g=gh, mw_p=mw, gap_gt_spread=gap > spread, gap_gt0=gap > 0)
        if boot:
            cells = {(dw, dty): x[(x.dow == dw) & (x.dt == dty)][["nightn", "total"]].values for dw in range(7) for dty in ("weekday", "weekend") if ((x.dow == dw) & (x.dt == dty)).any()}
            mg = np.empty(B)
            for b in range(B):
                num = {"weekday": 0.0, "weekend": 0.0}; den = {"weekday": 0.0, "weekend": 0.0}; ds = []
                for (dw, dty), arr in cells.items():
                    s_ = arr[rng3.integers(0, len(arr), len(arr))]; num[dty] += s_[:, 0].sum(); den[dty] += s_[:, 1].sum()
                    if dty == "weekday" and dw < 4: ds.append(s_[:, 0].sum() / s_[:, 1].sum())
                mg[b] = num["weekend"] / den["weekend"] - num["weekday"] / den["weekday"] - (max(ds) - min(ds))
            r["mlo"], r["mhi"] = np.percentile(mg, 2.5) * 100, np.percentile(mg, 97.5) * 100
        out.append(r)
    return pd.DataFrame(out)


def pooled_reg(g):
    d = g[g.dt.isin(["weekday", "weekend"])].copy(); d["we"] = (d.dt == "weekend").astype(float)
    f = smf.ols("share ~ we + C(month)", data=d).fit(cov_type="HC3")
    ci = f.conf_int().loc["we"]; return f.params["we"] * 100, ci[0] * 100, ci[1] * 100, len(d)


Q3P = {}
for s in SV:
    g = label(daytab(s, NIGHT)); Q3P[s] = g
    chk("Q3", f"{s} days", 365, len(g), 0, "recount"); chk("Q3", f"{s} weekday days", 250, int((g.dt == "weekday").sum()), 0, "recount")
    chk("Q3", f"{s} weekend days", 104, int((g.dt == "weekend").sum()), 0, "recount"); chk("Q3", f"{s} holiday weekdays excluded", 11, int((g.dt == "holiday").sum()), 0, "recount")
    chk("Q3", f"{s} trips total", {"yellow": 46494334, "fhvhv": 253409771}[s], int(g.total.sum()), 0, "DuckDB sum")
    m = monthly(g, boot=True)
    a = dec[dec.service == s].reset_index(drop=True)
    assert list(a.month) == list(m.month)
    for i, r in m.iterrows():
        ar_ = a.iloc[i]
        chk("Q3 monthly", f"{s} {r.month} gap_m pp", ar_.gap_pp, r.gap, 1e-7, "recomputed (pooled night/total)")
        chk("Q3 monthly", f"{s} {r.month} spread_m pp", ar_.spread_pp, r.spread, 1e-7, "recomputed (Mon-Thu pooled)")
        chk("Q3 monthly", f"{s} {r.month} weekday night share", ar_.night_share_weekday, r.sh_wd, 1e-9, "recomputed")
        chk("Q3 monthly", f"{s} {r.month} weekend night share", ar_.night_share_weekend, r.sh_we, 1e-9, "recomputed")
        chk("Q3 monthly", f"{s} {r.month} Welch t", ar_.welch_t, r.t, 1e-6, "scipy ttest_ind(equal_var=False)")
        chk("Q3 monthly", f"{s} {r.month} Hedges g", ar_.hedges_g, r.g, 1e-6, "own formula")
        chk("Q3 monthly", f"{s} {r.month} margin CI lo pp", ar_.margin_ci_lo_pp, r.mlo, 0.8, "own DOW-cell day bootstrap, seed 1003", "tol 0.8 pp (few days per cell)")
        chk("Q3 monthly", f"{s} {r.month} margin CI hi pp", ar_.margin_ci_hi_pp, r.mhi, 0.8, "own DOW-cell day bootstrap", "tol 0.8 pp")
        chk("Q3 monthly", f"{s} {r.month} Mann-Whitney one-sided p < 0.05 (non-parametric cross-check)", True, bool(r.mw_p < 0.05), None, "scipy mannwhitneyu", f"p={r.mw_p:.2e}")
    Q3P[(s, "m")] = m
allp = np.concatenate([Q3P[(s, "m")].p.values for s in SV])
# analyst order: concat service yellow then fhvhv -> same
holm24 = holm(allp)
print("Q3 largest Holm p (validator):", holm24.max(), " analyst max:", dec.p_holm.max())
chk("Q3", "largest Holm-adjusted p over 24 tests", float(dec.p_holm.max()), float(holm24.max()), 1e-6, "own Holm", note="analyst reports 0.00045")
for s in SV:
    g = Q3P[s]; m = Q3P[(s, "m")]
    chk("Q3", f"{s} months passing gap>0 and gap>spread", 12, int((m.gap_gt0 & m.gap_gt_spread).sum()), 0, "recount")
    mi = m.margin.idxmin()
    a = dec[(dec.service == s)]; am = a.loc[a.margin_pp.idxmin()]
    chk("Q3", f"{s} smallest margin pp", am.margin_pp, m.margin.min(), 1e-7, "recomputed", note=f"month {m.month[mi]}")
    c, lo, hi, n = pooled_reg(g)
    ra = reg_a[(reg_a.service == s) & (reg_a.variant == "primary")].iloc[0]
    chk("Q3", f"{s} pooled weekend effect pp", ra.coef_pp, c, 1e-6, "statsmodels formula API OLS + HC3")
    chk("Q3", f"{s} pooled CI lo", ra.ci_lo_pp, lo, 1e-6, "same"); chk("Q3", f"{s} pooled CI hi", ra.ci_hi_pp, hi, 1e-6, "same")
    chk("Q3", f"{s} gap range min pp", float(dec[dec.service == s].gap_pp.min()), float(m.gap.min()), 1e-7, "recomputed")
    chk("Q3", f"{s} gap range max pp", float(dec[dec.service == s].gap_pp.max()), float(m.gap.max()), 1e-7, "recomputed")
    chk("Q3", f"{s} spread range min pp", float(dec[dec.service == s].spread_pp.min()), float(m.spread.min()), 1e-7, "recomputed")
    chk("Q3", f"{s} spread range max pp", float(dec[dec.service == s].spread_pp.max()), float(m.spread.max()), 1e-7, "recomputed")
    chk("Q3", f"{s} weekday night share range min", 0, 0, 0, "n/a") if False else None
    print(s, "weekday share range", round(m.sh_wd.min() * 100, 2), round(m.sh_wd.max() * 100, 2), "weekend", round(m.sh_we.min() * 100, 2), round(m.sh_we.max() * 100, 2))
# sensitivities
VAR = {"S1_holidays_as_ordinary": lambda s: label(daytab(s, NIGHT), hol_weekday_ordinary=True),
       "S2_hour5_in_night": lambda s: label(daytab(s, NIGHT2)),
       "S3_literal_prev_day_Mon-Fri_vs_Sat-Sun": lambda s: label(daytab(s, NIGHT, shift=True)),
       "S3_intent_Fri-Sat_nights_weekend": lambda s: label(daytab(s, NIGHT, shift=True), fri_sat=True)}
for s in SV:
    for v, fn in VAR.items():
        g = fn(s); m = monthly(g); a = sens[(sens.service == s) & (sens.variant == v)]
        chk("Q3 sens", f"{s} {v} months gap>spread", int(a.gap_gt_spread.sum()), int(m.gap_gt_spread.sum()), 0, "recomputed (own S3 re-assignment)")
        chk("Q3 sens", f"{s} {v} months gap>0", int(a.gap_gt0.sum()), int(m.gap_gt0.sum()), 0, "recomputed")
        chk("Q3 sens", f"{s} {v} mean gap pp", float(a.gap_pp.mean()), float(m.gap.mean()), 1e-6, "recomputed")
        c, lo, hi, n = pooled_reg(g); ra = reg_a[(reg_a.service == s) & (reg_a.variant == v)].iloc[0]
        chk("Q3 sens", f"{s} {v} pooled effect pp", ra.coef_pp, c, 1e-6, "statsmodels formula OLS HC3", note=f"n_days a={ra.n_days} v={n}")
        if "S3" in v: print(s, v, "gap_gt_spread months:", m.month[m.gap_gt_spread].tolist() if False else int(m.gap_gt_spread.sum()))
# hourly profile spot check
hp_a = pd.read_csv(OUTS / "q3/q3_hourly_profile.csv")
for s in SV:
    d = cat(s, "dhp", Q123).groupby(["date", "hr"]).n.sum().unstack(fill_value=0)
    g = Q3P[s]
    for typ in ("weekday", "weekend"):
        days = d[g.dt.reindex(d.index).eq(typ).values]
        for hr in (3, 8, 18):
            a = hp_a[(hp_a.service == s) & (hp_a.day_type == typ) & (hp_a.hour == hr) & (hp_a.metric == "trips_per_day")].iloc[0]
            chk("Q3 hourly", f"{s} {typ} hour {hr} mean trips/day", a["mean"], days[hr].mean(), 1e-6 * a["mean"], "recomputed", kind="rel")

# ============ Q4 ============
print("\n==== Q4 ====")
q4 = pd.read_csv(OUTS / "q4/q4_share_results.csv"); q4m = pd.read_csv(OUTS / "q4/q4_monthly_share.csv"); s4 = pd.read_csv(OUTS / "q4/q4_sensitivity_S4.csv")
rng4 = np.random.default_rng(1004)
PW, PT = {}, {}
for s in SV:
    for y in (2023, 2024, 2026):
        f = cat(s, "flags", JS(y)); f["wk"] = week_of(f.date)
        f["valid"] = f.vpu & f.vdo
        f["num"] = np.where(f.valid & f.inz, f.n, 0); f["den"] = np.where(f.valid, f.n, 0); f["inz_all"] = np.where(f.inz, f.n, 0)
        w = f.groupby("wk")[["num", "den", "inz_all", "n"]].sum().sort_index(); PW[(s, y)] = w
        f["mo"] = f.date.dt.month; PT[(s, y)] = f.groupby("mo")[["num", "den"]].sum()
for s in SV:
    reps, reps4 = {}, {}
    for y in (2023, 2024, 2026):
        w = PW[(s, y)]; Wq = bweights(len(w), rng4)
        reps[y] = (Wq @ w.num.values) / (Wq @ w.den.values); reps4[y] = (Wq @ w.inz_all.values) / (Wq @ w.n.values)
        pt = w.num.sum() / w.den.sum()
        r = q4[(q4.service == s) & (q4.row_type == "period") & (q4.period == str(y))].iloc[0]
        chk("Q4", f"{s} {y} share", r.share, pt, 1e-9, "DuckDB flags; numerator/denominator")
        chk("Q4", f"{s} {y} in-zone trips", r.in_zone_trips, w.num.sum(), 0, "DuckDB"); chk("Q4", f"{s} {y} valid denominator", r.valid_denominator, w.den.sum(), 0, "DuckDB")
        chk("Q4", f"{s} {y} excluded share", r.excluded_share, 1 - w.den.sum() / w.n.sum(), 1e-9, "DuckDB")
        lo, hi = pctci(reps[y])
        chk("Q4", f"{s} {y} share CI lo", r.share_lo, lo, 0.0012, "own week bootstrap seed 1004", "tol 0.12 pp"); chk("Q4", f"{s} {y} share CI hi", r.share_hi, hi, 0.0012, "own week bootstrap")
        chk("Q4", f"{s} {y} weeks", r.weeks, len(w), 0, "recount")
    pt = {y: PW[(s, y)].num.sum() / PW[(s, y)].den.sum() for y in reps}
    dm, dd = pt[2026] - pt[2024], pt[2024] - pt[2023]
    rm, rd = reps[2026] - reps[2024], reps[2024] - reps[2023]
    for nm, ptv, rep in (("main", dm, rm), ("drift", dd, rd)):
        r = q4[(q4.service == s) & (q4.row_type == "delta") & (q4.period == nm)].iloc[0]
        chk("Q4", f"{s} Delta_{nm} pp", r.share * 100, ptv * 100, 1e-7, "recomputed")
        lo, hi = pctci(rep); chk("Q4", f"{s} Delta_{nm} CI lo pp", r.share_lo * 100, lo * 100, 0.12, "own bootstrap", "tol 0.12 pp"); chk("Q4", f"{s} Delta_{nm} CI hi pp", r.share_hi * 100, hi * 100, 0.12, "own bootstrap")
    r = q4[(q4.service == s) & (q4.row_type == "margin")].iloc[0]
    mg = abs(dm) - abs(dd); mrep = np.abs(rm) - np.abs(rd)
    chk("Q4", f"{s} |main|-|drift| pp", r.share * 100, mg * 100, 1e-7, "recomputed")
    lo, hi = pctci(mrep); chk("Q4", f"{s} margin CI lo pp", r.share_lo * 100, lo * 100, 0.15, "own bootstrap", "tol 0.15 pp"); chk("Q4", f"{s} margin CI hi pp", r.share_hi * 100, hi * 100, 0.15, "own bootstrap")
    r = q4[(q4.service == s) & (q4.row_type == "relative_change")].iloc[0]
    chk("Q4", f"{s} relative change main", r.share, dm / pt[2024], 1e-9, "recomputed")
    p = (1 + (rm >= 0).sum()) / (B + 1)
    Q4P = q4[(q4.service == s) & (q4.row_type == "delta") & (q4.period == "main")].iloc[0]
    chk("Q4", f"{s} one-sided raw p (main<0)", Q4P.p_one_sided_raw, p, 0.0005, "own bootstrap +1 rule", "both at floor")
    chk("Q4", f"{s} decision (|main|>|drift|)", "real shift", "real shift" if mg > 0 else "keep", None, "decision rule")
    # S4
    a4 = s4[s4.service == s].iloc[0]; p4 = {y: PW[(s, y)].inz_all.sum() / PW[(s, y)].n.sum() for y in reps}
    chk("Q4 S4", f"{s} S4 share 2023", a4.share2023_S4, p4[2023], 1e-9, "recomputed"); chk("Q4 S4", f"{s} S4 share 2024", a4.share2024_S4, p4[2024], 1e-9, "recomputed"); chk("Q4 S4", f"{s} S4 share 2026", a4.share2026_S4, p4[2026], 1e-9, "recomputed")
    m4 = abs(p4[2026] - p4[2024]) - abs(p4[2024] - p4[2023]); chk("Q4 S4", f"{s} S4 margin pp", a4.margin_S4 * 100, m4 * 100, 1e-7, "recomputed")
    # monthly
    for y in (2023, 2024, 2026):
        for mo in range(1, 10):
            a_ = q4m[(q4m.service == s) & (q4m.year == y) & (q4m.month == mo)].iloc[0]
            t = PT[(s, y)].loc[mo]; CHK.append({"group": "Q4 monthly", "number": f"{s} {y}-{mo:02d} share", "analyst": a_.share, "validator": t.num / t.den, "method": "recomputed", "tol": 1e-9, "pass": abs(a_.share - t.num / t.den) <= 1e-9, "note": ""})
    # leave-one-month-out sensitivity of the decision margin
    flips = []
    for drop in range(1, 10):
        sh = {}
        for y in (2023, 2024, 2026):
            t = PT[(s, y)].drop(index=drop); sh[y] = t.num.sum() / t.den.sum()
        flips.append((drop, abs(sh[2026] - sh[2024]) - abs(sh[2024] - sh[2023])))
    print(s, "leave-one-month-out margin (pp) min/max", round(min(f[1] for f in flips) * 100, 2), round(max(f[1] for f in flips) * 100, 2), "decision stable:", all(f[1] > 0 for f in flips))
    # Excluding-month-class: Jan-May vs Jun-Sep delta main
    for lab, mos in (("Jan-May", range(1, 6)), ("Jun-Sep", range(6, 10))):
        sh = {y: PT[(s, y)].loc[list(mos)].num.sum() / PT[(s, y)].loc[list(mos)].den.sum() for y in (2023, 2024, 2026)}
        print(s, lab, "share 2023/24/26", [round(sh[y] * 100, 2) for y in sh], "delta main pp", round((sh[2026] - sh[2024]) * 100, 2), "drift pp", round((sh[2024] - sh[2023]) * 100, 2))
for pv, s in zip(holm([float(q4[(q4.service == s) & (q4.row_type == "delta") & (q4.period == "main")].p_one_sided_raw.iloc[0]) for s in SV]), SV):
    r = q4[(q4.service == s) & (q4.row_type == "delta") & (q4.period == "main")].iloc[0]
    chk("Q4", f"{s} Holm p (2 tests)", r.p_holm, pv, 0.0005, "own Holm")
# fee cross-check
fc = pd.read_csv(OUTS / "q4/q4_fee_crosscheck.csv")
for s in SV:
    f = cat(s, "fee", Q123); f["wk"] = week_of(f.date); f["pos"] = f.fs == 2
    fp = f[f.pos].n.sum(); inz = f[f.inz].n.sum(); both = f[f.pos & f.inz].n.sum()
    a = fc[fc.service == s].iloc[0]
    chk("Q4 fee", f"{s} fee>0 trips", a.fee_positive, fp, 0, "DuckDB"); chk("Q4 fee", f"{s} in-zone trips", a.in_zone_trips, inz, 0, "DuckDB")
    chk("Q4 fee", f"{s} fee null trips", a.fee_null, f[f.fs == 0].n.sum(), 0, "DuckDB")
    chk("Q4 fee", f"{s} (i) share of fee trips with in-zone end", a.i_share_of_fee_trips_with_inzone_end, both / fp, 1e-9, "recomputed")
    chk("Q4 fee", f"{s} (ii) share of in-zone trips with fee", a.ii_share_of_inzone_trips_with_fee, both / inz, 1e-9, "recomputed")
    w = f.assign(p_=np.where(f.pos, f.n, 0), i_=np.where(f.inz, f.n, 0), b_=np.where(f.pos & f.inz, f.n, 0)).groupby("wk")[["p_", "i_", "b_"]].sum()
    Wq = bweights(len(w), np.random.default_rng(1005)); ir = (Wq @ w.b_.values) / (Wq @ w.p_.values); iir = (Wq @ w.b_.values) / (Wq @ w.i_.values)
    lo, hi = pctci(ir); chk("Q4 fee", f"{s} (i) CI lo", a.i_lo, lo, 0.002, "own bootstrap"); chk("Q4 fee", f"{s} (i) CI hi", a.i_hi, hi, 0.002, "own bootstrap")
    lo, hi = pctci(iir); chk("Q4 fee", f"{s} (ii) CI lo", a.ii_lo, lo, 0.003, "own bootstrap"); chk("Q4 fee", f"{s} (ii) CI hi", a.ii_hi, hi, 0.003, "own bootstrap")
    # zone-level fee share 2026
    z = f[f.date.dt.year == 2026].groupby("pu").apply(lambda x: pd.Series({"p": x.n.sum(), "f": x.n[x.pos].sum()}), include_groups=False); z["sh"] = z.f / z.p
    inl = z[z.index.isin(CRZ) & (z.sh < 0.5)]; outh = z[~z.index.isin(CRZ) & (z.sh > 0.5) & z.index.isin(VALID)]
    zfa = pd.read_csv(OUTS / "q4/q4_fee_share_by_pickup_zone_2026.csv"); zfa = zfa[zfa.service == s]
    chk("Q4 fee", f"{s} CRZ-list zones with fee share <50%", 0, len(inl), 0, "recomputed")
    na = int(((~zfa.in_crz_list) & (zfa.fee_share > 0.5) & zfa.pu.isin(VALID)).sum())
    chk("Q4 fee", f"{s} outside-list zones with fee share >50%", na, len(outh), 0, "recomputed", note=str(sorted(outh.index.tolist())))
# neighbours + supplementary
import geopandas as gpd
sh = gpd.read_file(ROOT / "data/taxi_zones.shp"); sh = sh.set_index("LocationID")
crzg = sh.loc[sorted(CRZ)].geometry.union_all()
nbr = sorted(int(i) for i, g_ in sh.geometry.items() if i not in CRZ and g_.intersects(crzg))
nbr_a = sorted(pd.read_csv(OUTS / "reference/crz_neighbour_zone_ids.csv").LocationID.tolist())
chk("Q4 neighbours", "neighbour zone IDs (geometry, no tolerance)", str(nbr_a), str(nbr), None, "geopandas union.intersects (analyst: pairwise intersects)")
nsup = pd.read_csv(OUTS / "q4/q4_neighbour_zone_share_change.csv")
for s in SV:
    for kind in ("pickup", "dropoff"):
        shr = {}
        for y in (2024, 2026):
            if kind == "pickup":
                d = cat(s, "dhp", JS(y)); v = d[d.pu.isin(VALID)].groupby("pu").n.sum()
            else:
                d = cat(s, "do", JS(y)); v = d[d.dof.isin(VALID)].groupby("dof").n.sum()
            shr[y] = v / v.sum()
        comb24 = shr[2024].reindex(nbr).sum(); comb26 = shr[2026].reindex(nbr).sum()
        a = nsup[(nsup.service == s) & (nsup.kind == kind)]
        chk("Q4 neighbours", f"{s} {kind} neighbour combined share 2024", a.share2024.sum(), comb24, 1e-9, "recomputed"); chk("Q4 neighbours", f"{s} {kind} neighbour combined share 2026", a.share2026.sum(), comb26, 1e-9, "recomputed")
        chk("Q4 neighbours", f"{s} {kind} neighbour change pp", a.delta_pp.sum(), (comb26 - comb24) * 100, 1e-7, "recomputed")
        crz24 = shr[2024].reindex(sorted(CRZ)).sum(); crz26 = shr[2026].reindex(sorted(CRZ)).sum()
        if kind == "pickup": chk("Q4 neighbours", f"{s} 38-zone combined pickup share change pp", {"yellow": -2.53, "fhvhv": -2.98}[s], (crz26 - crz24) * 100, 0.006, "recomputed", "analyst rounded to 2 dp")
        # top-15 gains check
        sup = pd.read_csv(OUTS / "q4/q4_supplementary_top15_gains_losses.csv"); sup = sup[(sup.service == s) & (sup.kind == kind)]
        dlt = ((shr[2026].reindex(VALID, fill_value=0) - shr[2024].reindex(VALID, fill_value=0)) * 100); dlt = dlt[~dlt.index.isin(CRZ)]
        g15 = list(dlt.sort_values(ascending=False).index[:15]); a15 = list(sup[sup.direction == "gain"].sort_values("delta_pp", ascending=False).zone_id)
        chk("Q4 supplementary", f"{s} {kind} top-15 gain zone set", str(sorted(a15)), str(sorted(int(i) for i in g15)), None, "recomputed")
fsum = pd.DataFrame(CHK)
fsum.to_csv(LOG / "validation_checks.csv", index=False)
print("\nTOTAL checks", len(fsum), "FAIL", int((~fsum["pass"]).sum()))
print(fsum[~fsum["pass"]].to_string())
