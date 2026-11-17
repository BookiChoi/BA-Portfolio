"""Impact model for the 09 recommendations (R1, R2, R3) of nyc-congestion-pricing.

Run (from the project folder):  python pipeline/impact_model.py
Writes: outputs/impact_results.json; the printed output is the evidence
(copy in outputs/impact_model.log).

Inputs: only (a) the human's assumption tables in workflow/09_recommendations.md,
(b) numbers that are PASS in workflow/06_validation.md, (c) clearly marked modeler
placeholders (noise levels) that no file supplies. Nothing is read from data/.

Why a closed-form power calculation plus a small simulation: there is no driver-level data in
this project, so the pilot cannot be simulated from data; the formula is cross-checked by a
simulation of the same assumed noise model.
"""
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

OUT = Path(__file__).resolve().parents[1] / "outputs"
ALPHA, POWER = 0.05, 0.80
ZA, ZB = norm.ppf(1 - ALPHA / 2), norm.ppf(POWER)
RES = {}


def hdr(t):
    print("\n" + "=" * 8, t)


# ---------------------------------------------------------------- R1
# Human assumptions (09, R1 table): drivers per group, follow share, effect among followers, weeks.
R1 = {
    "n": (20, 50, 100), "follow": (0.30, 0.50, 0.70),
    "eff": (0.00, 0.03, 0.08), "weeks": (8, 8, 12),
}
# Modeler placeholders (NOT in any file; flagged as unsourced in 10_impact.md):
# sigma_b = between-driver SD of mean trips per driver-hour, as a fraction of the mean;
# sigma_w = week-to-week SD within a driver, as a fraction of the mean.
NUIS = {"sigma_b": (0.15, 0.20, 0.30), "sigma_w": (0.30, 0.40, 0.50)}


def resid_sd(sb, sw, weeks):
    """SD of a driver's pilot-period mean after adjusting for an equally long pre-period mean (ANCOVA).
    total var = sb^2 + sw^2/T; correlation of the two means rho = sb^2/total; residual = total*(1-rho^2)."""
    tot = sb ** 2 + sw ** 2 / weeks
    rho = sb ** 2 / tot
    return math.sqrt(tot * (1 - rho ** 2)), rho


def se_diff(n, sb, sw, weeks):
    s, _ = resid_sd(sb, sw, weeks)
    return s * math.sqrt(2.0 / n)


def mde(n, sb, sw, weeks):
    return (ZA + ZB) * se_diff(n, sb, sw, weeks)


def n_per_arm(delta, sb, sw, weeks):
    s, _ = resid_sd(sb, sw, weeks)
    return 2 * ((ZA + ZB) * s / delta) ** 2


def p_success(itt, n, sb, sw, weeks, rule=0.03):
    """P(estimate >= rule AND lower 95% bound > 0), normal approximation."""
    se = se_diff(n, sb, sw, weeks)
    thr = max(rule, ZA * se)
    return 1 - norm.cdf((thr - itt) / se)


def r1_point(n, f, e, w, sb, sw):
    itt = f * e
    return dict(itt=itt, se=se_diff(n, sb, sw, w), mde_itt=mde(n, sb, sw, w),
                mde_followers=mde(n, sb, sw, w) / f, p_success=p_success(itt, n, sb, sw, w),
                p_detect_itt=1 - norm.cdf(ZA - itt / se_diff(n, sb, sw, w)) if itt > 0 else ALPHA / 2)


hdr("R1 scenarios (nuisance at base: sigma_b=0.20, sigma_w=0.40)")
sb0, sw0 = NUIS["sigma_b"][1], NUIS["sigma_w"][1]
R1_scen = {}
for i, name in enumerate(["low", "base", "high"]):
    n, f, e, w = (R1[k][i] for k in ("n", "follow", "eff", "weeks"))
    r = r1_point(n, f, e, w, sb0, sw0)
    s, rho = resid_sd(sb0, sw0, w)
    r.update(n=n, follow=f, eff=e, weeks=w, resid_sd=s, rho=rho)
    R1_scen[name] = r
    print(name, {k: round(v, 4) for k, v in r.items()})
RES["R1_scenarios"] = R1_scen

hdr("R1 required sample size per group (alpha .05 two-sided, power .80, ANCOVA, base nuisance)")
req = {}
for w in (8, 12):
    for d in (0.03, 0.015, 0.056):
        req[f"weeks{w}_delta{d}"] = n_per_arm(d, sb0, sw0, w)
        print(f"weeks={w} detectable ITT delta={d:.3f}: n per group = {req[f'weeks{w}_delta{d}']:.0f}")
RES["R1_required_n"] = req
print("MDE (ITT) at human's group sizes, 8 weeks:",
      {n: round(mde(n, sb0, sw0, 8), 4) for n in (20, 50, 100)})
print("MDE (ITT) at human's group sizes, 12 weeks:",
      {n: round(mde(n, sb0, sw0, 12), 4) for n in (20, 50, 100)})
RES["R1_mde_8w"] = {n: mde(n, sb0, sw0, 8) for n in (20, 50, 100)}
RES["R1_mde_12w"] = {n: mde(n, sb0, sw0, 12) for n in (20, 50, 100)}

hdr("R1 simulation cross-check of the formula (base scenario, 4000 reps)")
rng = np.random.default_rng(2026)


def simulate(n, itt, sb, sw, weeks, reps=4000):
    wins = 0
    est_all = []
    for _ in range(reps):
        d_pre = rng.normal(0, sb, 2 * n)           # driver level (relative to mean 1)
        pre = 1 + d_pre + rng.normal(0, sw / math.sqrt(weeks), 2 * n)
        trt = np.r_[np.zeros(n), np.ones(n)]
        post = 1 + d_pre + itt * trt + rng.normal(0, sw / math.sqrt(weeks), 2 * n)
        X = np.c_[np.ones(2 * n), trt, pre]
        beta, *_ = np.linalg.lstsq(X, post, rcond=None)
        res = post - X @ beta
        s2 = res @ res / (2 * n - 3)
        cov = s2 * np.linalg.inv(X.T @ X)
        se = math.sqrt(cov[1, 1])
        est_all.append(beta[1])
        if beta[1] >= 0.03 and beta[1] - ZA * se > 0:
            wins += 1
    return wins / reps, float(np.std(est_all))


for name in ("low", "base", "high"):
    r = R1_scen[name]
    ps, sd = simulate(r["n"], r["itt"], sb0, sw0, r["weeks"])
    r["sim_p_success"], r["sim_se"] = ps, sd
    print(f"{name}: formula p_success={r['p_success']:.3f} sim={ps:.3f}; formula SE={r['se']:.4f} sim SD={sd:.4f}")

hdr("R1 sensitivity (one at a time, others at base): ITT effect and P(success)")
base_args = dict(n=50, f=0.5, e=0.03, w=8, sb=sb0, sw=sw0)
rows = []
spec = [("n", R1["n"], "drivers per group"), ("f", R1["follow"], "follow share"),
        ("e", R1["eff"], "effect among followers"), ("w", R1["weeks"], "pilot weeks"),
        ("sb", NUIS["sigma_b"], "between-driver SD (placeholder)"),
        ("sw", NUIS["sigma_w"], "weekly SD (placeholder)")]
for key, vals, label in spec:
    out = {}
    for tag, v in (("low", vals[0]), ("high", vals[2])):
        a = dict(base_args)
        a[key] = v
        out[tag] = p_success(a["f"] * a["e"], a["n"], a["sb"], a["sw"], a["w"])
        out[tag + "_itt"] = a["f"] * a["e"]
    swing = abs(out["high"] - out["low"])
    rows.append((swing, label, vals, out))
rows.sort(key=lambda r: -r[0])
for swing, label, vals, out in rows:
    print(f"{label:35s} low={vals[0]} high={vals[2]}  P(success) low={out['low']:.3f} high={out['high']:.3f} swing={swing:.3f}")
RES["R1_sensitivity"] = [dict(param=l, low=v[0], high=v[2], p_low=o["low"], p_high=o["high"], swing=s,
                              itt_low=o["low_itt"], itt_high=o["high_itt"]) for s, l, v, o in rows]
print("Base P(success) with all at base:", round(p_success(0.015, 50, sb0, sw0, 8), 4))
print("Compliance needed for ITT=3% at effect among followers 3/8%: ",
      {e: round(0.03 / e, 3) for e in (0.03, 0.08)})

# ---------------------------------------------------------------- R2
hdr("R2 scenarios")
R2 = {"N": (100, 300, 600), "use": (0.40, 0.60, 0.80), "pp": (0.0, 2.0, 5.0)}
SD_SHARE = (5.0, 8.0, 12.0)   # modeler placeholder: SD across drivers of the weekend-night hour share, pp
R2_scen = {}
for i, name in enumerate(["low", "base", "high"]):
    N, u, pp = R2["N"][i], R2["use"][i], R2["pp"][i]
    R2_scen[name] = dict(N=N, use=u, pp=pp, users=N * u,
                         group_shift_A=u * pp,   # reading A: pp applies to users only
                         group_shift_B=pp,       # reading B: pp is the cohort average
                         meets_2pp_A=(u * pp) >= 2.0, meets_2pp_B=pp >= 2.0)
    print(name, R2_scen[name])
RES["R2_scenarios"] = R2_scen
s = SD_SHARE[1]
r2d = {}
for N in (100, 300, 600):
    r2d[f"cohort_vs_previous_N{N}"] = (ZA + ZB) * s * math.sqrt(2 / N)
    r2d[f"randomised_split_N{N}"] = (ZA + ZB) * s * math.sqrt(2 / (N / 2))
for k, v in r2d.items():
    print(f"MDE (pp) {k}: {v:.2f}  (SD={s} pp)")
RES["R2_mde_pp"] = r2d
r2n = {}
for sd in SD_SHARE:
    for d in (2.0, 1.2, 5.0):
        r2n[f"sd{sd}_delta{d}"] = 2 * ((ZA + ZB) * sd / d) ** 2
        print(f"SD={sd} pp, detect {d} pp: n per arm = {r2n[f'sd{sd}_delta{d}']:.0f}")
RES["R2_required_n"] = r2n
# Sensitivity of group-level shift (reading A): swing in pp
hdr("R2 sensitivity of group-level shift (reading A), others at base")
base = dict(N=300, u=0.6, pp=2.0)
sens2 = []
for key, lo, hi, label in (("u", 0.4, 0.8, "use share"), ("pp", 0.0, 5.0, "shift among users (pp)"),
                           ("N", 100, 600, "new drivers per quarter")):
    def shift(v):
        a = dict(base); a[key] = v
        return a["u"] * a["pp"], a["N"] * a["u"] * a["pp"] / 100  # pp; driver-equivalents shifted by 1 pp = N*shift/100
    sens2.append(dict(param=label, low=lo, high=hi, group_pp_low=shift(lo)[0], group_pp_high=shift(hi)[0],
                      driver_equiv_low=shift(lo)[1], driver_equiv_high=shift(hi)[1]))
    print(sens2[-1])
RES["R2_sensitivity"] = sens2
# Count-vs-share break-even from PASS numbers in 06/05 (night share ranges by day type)
hdr("R2 share vs count break-even (weekend daily volume as a fraction of weekday daily volume)")
SH = {"yellow": dict(wd=(13.0, 15.9), we=(25.6, 29.3)), "hvfhv": dict(wd=(16.2, 18.5), we=(26.3, 28.5))}
be = {}
for sv, d in SH.items():
    wd_mid, we_mid = sum(d["wd"]) / 2, sum(d["we"]) / 2
    be[sv] = dict(best=d["wd"][0] / d["we"][1], mid=wd_mid / we_mid, worst=d["wd"][1] / d["we"][0])
    print(sv, {k: round(v, 3) for k, v in be[sv].items()})
RES["R2_breakeven_volume_ratio"] = be

# ---------------------------------------------------------------- R3
hdr("R3 effort and delay")
R3 = {"days": (5, 10, 20), "delay": (2, 4, 8)}
RES["R3_effort"] = R3
print(R3)
hdr("R3 what the follow-up could show: Q4 margin if the 2023-2024 drift continues for 2 years")
# PASS numbers from 05/06: Delta_main and Delta_drift with 95% CI (pp)
Q4 = {"yellow": dict(main=-1.99, mci=(-2.77, -1.23), drift=-0.18, dci=(-0.70, 0.33)),
      "hvfhv": dict(main=-4.26, mci=(-4.80, -3.75), drift=-1.69, dci=(-2.18, -1.19))}
q4 = {}
for sv, d in Q4.items():
    se_m = (d["mci"][1] - d["mci"][0]) / (2 * ZA)
    se_d = (d["dci"][1] - d["dci"][0]) / (2 * ZA)
    q4[sv] = {}
    for k in (1.0, 1.5, 2.0):   # k = number of drift-years assumed to continue between 2024 and 2026
        resid = d["main"] - k * d["drift"]
        se = math.sqrt(se_m ** 2 + (k * se_d) ** 2)
        q4[sv][k] = dict(resid=resid, lo=resid - ZA * se, hi=resid + ZA * se)
        print(sv, "k=", k, {a: round(b, 2) for a, b in q4[sv][k].items()})
RES["R3_trend_scenarios"] = {sv: {str(k): v for k, v in d.items()} for sv, d in q4.items()}
print("Note: yellow Jun-Sep margin about 0 (06 F3: 2026 vs 2024 -0.40 pp, drift -0.34 pp).")

(OUT / "impact_results.json").write_text(json.dumps(RES, indent=2, default=float))
print("\nwrote", OUT / "impact_results.json")
