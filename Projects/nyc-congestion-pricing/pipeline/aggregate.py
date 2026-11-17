"""Per-file aggregation (plan section 0, 'Processing'): one file at a time, only the needed columns.

Every table is a count table, so later steps can resample calendar weeks without re-reading trips.
"""
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from . import config as C


def _groupcount(tbl: pa.Table, keys):
    g = tbl.group_by(keys).aggregate([([], "count_all")])
    return g.rename_columns(keys + ["n"]).to_pandas()


def aggregate_file(service, ym, valid_ids, crz_ids):
    """Return (tables dict, counts dict) for one file.

    Why these tables:
      dhp      (date, hour, pu)         -> Q1 day-parts and rankings, Q3 hourly shape, Q4 pickup marginals
      flags    (date, vpu, vdo, inzone) -> Q4 share, S4 denominators
      do_date  (date, do)               -> Q4 supplementary dropoff shares
      airport  (date, pu, do)           -> Q2, only rows with an airport pickup
      fee      (date, pu, vdo, inzone, fee_state) -> Q4 fee cross-check (files with cbd_congestion_fee only)
    Invalid or null IDs are kept as codes (-1 for null) and flagged, never silently dropped, so exclusions can be counted.
    """
    path = C.parquet_path(service, ym)
    pf = pq.ParquetFile(path)
    names = set(pf.schema_arrow.names)
    has_fee = "cbd_congestion_fee" in names
    cols = [C.PICKUP_COL[service], "PULocationID", "DOLocationID"] + (["cbd_congestion_fee"] if has_fee else [])
    t = pq.read_table(path, columns=cols)
    n_total = t.num_rows
    pk = t[C.PICKUP_COL[service]]
    n_null_pickup = pk.null_count
    in_month = pc.and_(pc.equal(pc.year(pk), ym[0]), pc.equal(pc.month(pk), ym[1]))
    in_month = pc.fill_null(in_month, False)  # null pickup -> not in month (counted above)
    t = t.filter(in_month)
    n_in_month = t.num_rows

    pu = pc.fill_null(t["PULocationID"].cast(pa.int64()), -1)
    do = pc.fill_null(t["DOLocationID"].cast(pa.int64()), -1)
    n_null_pu = t["PULocationID"].null_count
    n_null_do = t["DOLocationID"].null_count
    valid = pa.array(sorted(valid_ids), pa.int64())
    crz = pa.array(sorted(crz_ids), pa.int64())
    vpu = pc.is_in(pu, value_set=valid)
    vdo = pc.is_in(do, value_set=valid)
    # in-zone only if the ID is a valid CRZ ID; CRZ IDs are a subset of valid IDs (checked in step 2)
    inzone = pc.or_(pc.is_in(pu, value_set=crz), pc.is_in(do, value_set=crz))
    date = pc.cast(t[C.PICKUP_COL[service]], pa.date32())
    hour = pc.hour(t[C.PICKUP_COL[service]])

    base = pa.table({"date": date, "hour": hour, "pu": pu, "do": do, "vpu": vpu, "vdo": vdo, "inzone": inzone})
    tabs = {
        "dhp": _groupcount(base.select(["date", "hour", "pu"]), ["date", "hour", "pu"]),
        "flags": _groupcount(base.select(["date", "vpu", "vdo", "inzone"]), ["date", "vpu", "vdo", "inzone"]),
        "do_date": _groupcount(base.select(["date", "do"]), ["date", "do"]),
    }
    ap = base.filter(pc.is_in(base["pu"], value_set=pa.array(list(C.AIRPORTS), pa.int64())))
    tabs["airport"] = _groupcount(ap.select(["date", "pu", "do"]), ["date", "pu", "do"])
    if has_fee:
        fee = t["cbd_congestion_fee"]
        # state 0 = null (treated as no fee, counted separately), 1 = zero or negative, 2 = positive
        st = pc.if_else(pc.is_null(fee), 0, pc.if_else(pc.greater(pc.fill_null(fee, 0.0), 0.0), 2, 1))
        fb = base.append_column("fee_state", st.cast(pa.int8()))
        tabs["fee"] = _groupcount(fb.select(["date", "pu", "vdo", "inzone", "fee_state"]),
                                  ["date", "pu", "vdo", "inzone", "fee_state"])
    counts = {"rows_total": n_total, "null_pickup": n_null_pickup, "out_of_month": n_total - n_null_pickup - n_in_month,
              "rows_in_month": n_in_month, "null_pu": n_null_pu, "null_do": n_null_do,
              "invalid_pu": int(n_in_month - pc.sum(vpu).as_py()), "invalid_do": int(n_in_month - pc.sum(vdo).as_py())}
    return tabs, counts
