import pickle, pandas as pd
ROOT = "/Users/booki/Desktop/BA-Portfolio/Projects/nyc-congestion-pricing"
res = pickle.load(open(ROOT + "/workflow/logs/validation_cache/agg.pkl", "rb"))
lk = set(pd.read_csv(ROOT + "/data/taxi_zone_lookup.csv").LocationID)
for svc in ("yellow", "fhvhv"):
    for y in (2023, 2024, 2026):
        tot = 0; badpu = 0; baddo = 0; n264_pu = 0; n264_do = 0
        for m in range(1, 10):
            r = res[(svc, y, m)]
            d = r["dhp"].groupby("pu").n.sum(); o = r["do"].groupby("dof").n.sum()
            tot += d.sum(); badpu += d[~d.index.isin(lk)].sum(); baddo += o[~o.index.isin(lk)].sum()
            n264_pu += d[d.index.isin([264, 265])].sum(); n264_do += o[o.index.isin([264, 265])].sum()
        print(svc, y, "trips", int(tot), "PU not in lookup", int(badpu), "DO not in lookup", int(baddo), "PU 264/265 share %.4f%%" % (100 * n264_pu / tot), "DO 264/265 share %.4f%%" % (100 * n264_do / tot))
