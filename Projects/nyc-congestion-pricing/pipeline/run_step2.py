"""Step 2: lookup, airport list, CRZ list (38 IDs), neighbour zones from the shapefile, holiday list.

Writes the zone lists and the holiday list to outputs/ BEFORE any result is computed (plan requirement).
"""
import json

import geopandas as gpd
import pandas as pd

from . import config as C, load as L


HOLIDAYS = [  # fixed in plan section 5 (Q3), before results
    ("2025-10-13", "Columbus Day"), ("2025-11-11", "Veterans Day"), ("2025-11-27", "Thanksgiving"),
    ("2025-12-25", "Christmas Day"), ("2026-01-01", "New Year's Day"), ("2026-01-19", "Martin Luther King Jr. Day"),
    ("2026-02-16", "Presidents Day"), ("2026-05-25", "Memorial Day"), ("2026-06-19", "Juneteenth"),
    ("2026-07-03", "Independence Day (observed, 4 July 2026 is a Saturday)"), ("2026-09-07", "Labor Day")]


def main():
    lk = L.read_lookup()
    print("lookup columns:", list(lk.columns), "rows:", len(lk), "distinct IDs:", lk.LocationID.nunique())
    assert {"LocationID", "Borough", "Zone"} <= set(lk.columns), "STOP: lookup columns missing"
    print("\nlookup rows with Unknown / N/A / Outside of NYC labels:")
    print(lk[lk.Borough.isin(["Unknown", "N/A"]) | lk.Zone.isin(["Unknown", "N/A", "Outside of NYC"])].to_string(index=False))
    bad = L.invalid_zone_ids(lk)
    print("invalid zone IDs fixed from lookup:", bad)

    print("\nairport zones (plan: 1, 132, 138):")
    ap = lk[lk.LocationID.isin(C.AIRPORTS)]
    print(ap.to_string(index=False))
    for i, name in C.AIRPORTS.items():
        assert lk.loc[lk.LocationID == i, "Zone"].iloc[0] == name, f"STOP: airport {i} name mismatch"
    print("airport names match the plan")

    crz = pd.read_csv(C.CRZ_FILE)
    print("\nCRZ file columns:", list(crz.columns), "rows:", len(crz))
    ids = crz["Taxi Zone"].astype(int)
    assert ids.nunique() == 38 and len(crz) == 38, "STOP: CRZ list must have 38 distinct IDs"
    assert set(ids) <= set(lk.LocationID), "STOP: CRZ IDs not all in lookup"
    assert not (set(ids) & {264, 265}), "STOP: CRZ contains 264/265"
    crz_df = lk[lk.LocationID.isin(ids)].sort_values("LocationID")[["LocationID", "Borough", "Zone"]]
    print("CRZ zones (38):")
    print(crz_df.to_string(index=False))
    print("boroughs of CRZ zones:", crz_df.Borough.value_counts().to_dict())

    out = C.OUT / "reference"
    out.mkdir(parents=True, exist_ok=True)
    crz_df.to_csv(out / "crz_zone_ids.csv", index=False)
    pd.DataFrame([{"LocationID": i, "Zone": n} for i, n in C.AIRPORTS.items()]).to_csv(out / "airport_zone_ids.csv", index=False)
    pd.DataFrame(HOLIDAYS, columns=["date", "holiday"]).to_csv(out / "holidays_excluded_weekdays.csv", index=False)
    (out / "invalid_zone_ids.json").write_text(json.dumps({"invalid_ids": bad}) + "\n")
    print("\nwritten reference lists to", out)

    # Open item B: neighbours by geometry, no tolerance. Shares at least one boundary point = touches/intersects.
    shp = gpd.read_file(C.SHAPEFILE)
    print("\nshapefile columns:", list(shp.columns), "rows:", len(shp), "CRS:", shp.crs)
    idcol = "LocationID"
    assert idcol in shp.columns
    # Several shapefile rows can share one LocationID (multi-part zones); dissolve so the geometry per ID is complete.
    shp = shp.dissolve(by=idcol, as_index=False)
    print("distinct IDs in shapefile:", shp[idcol].nunique())
    missing = sorted(set(crz_df.LocationID) - set(shp[idcol]))
    print("CRZ IDs missing in shapefile:", missing)
    crz_geom = shp[shp[idcol].isin(crz_df.LocationID)]
    rest = shp[~shp[idcol].isin(crz_df.LocationID) & ~shp[idcol].isin([264, 265])]
    nbr = []
    for _, r in rest.iterrows():
        # intersects(): shares at least one point (boundary or interior), tolerance 0, as the human specified.
        if crz_geom.geometry.intersects(r.geometry).any():
            nbr.append(int(r[idcol]))
    nb = lk[lk.LocationID.isin(nbr)].sort_values("LocationID")[["LocationID", "Borough", "Zone"]]
    print(f"neighbouring zones (not in CRZ list, share >= 1 boundary point with a CRZ zone): {len(nb)}")
    print(nb.to_string(index=False))
    nb.to_csv(out / "crz_neighbour_zone_ids.csv", index=False)
    # Zones with no neighbour among CRZ zones would be reported; check that each CRZ zone has at least one non-CRZ neighbour
    isolated = [int(i) for i in crz_geom[idcol] if not rest.geometry.intersects(crz_geom[crz_geom[idcol] == i].geometry.iloc[0]).any()]
    print("CRZ zones with no outside neighbour:", isolated)


if __name__ == "__main__":
    main()
