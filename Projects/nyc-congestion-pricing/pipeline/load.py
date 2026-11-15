"""Step 1 and 2 of the plan: metadata-only file check, manifest, lookup and zone lists."""
import hashlib
import json

import pandas as pd
import pyarrow.parquet as pq

from . import config as C


def sha256(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def inspect_file(service, ym):
    """Read schema and footer metadata only (no row data), as step 1 requires."""
    p = C.parquet_path(service, ym)
    pf = pq.ParquetFile(p)
    cols = {f.name: str(f.type) for f in pf.schema_arrow}
    return {"service": service, "year": ym[0], "month": ym[1], "path": p,
            "rows": pf.metadata.num_rows, "bytes": p.stat().st_size, "cols": cols}


def read_lookup():
    return pd.read_csv(C.LOOKUP_FILE)


def invalid_zone_ids(lk):
    """IDs that are not real NYC zones: labelled Unknown / N/A / Outside of NYC in the lookup."""
    bad = lk[lk["Borough"].isin(["Unknown", "N/A"]) | lk["Zone"].isin(["Unknown", "N/A", "Outside of NYC"])]
    return sorted(bad["LocationID"].tolist())


def write_manifest(entries, path=C.ROOT / "data_manifest.json"):
    old = json.loads(path.read_text())
    old["datasets"] = entries
    path.write_text(json.dumps(old, indent=2) + "\n")
