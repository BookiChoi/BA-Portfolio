"""Load the seven Netflix reports and the IMDb dataset files.

All raw files stay outside the repo (paths come from the caller). Nothing here writes to the
source folders. Reading code for the xlsx layout is reused from ``profile_reports`` (same
project, already unit-tested) instead of being copied.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from pipeline.profile_reports import canonicalize, load_sheet
import openpyxl

NETFLIX_DIR = Path("~/Downloads/netflix-reports").expanduser()
IMDB_DIR = Path("~/Downloads/imdb-datasets").expanduser()

# Fixed order = calendar order. Why: Q1 is about alternation by position, so the order of the
# seven halves is part of the definition and must not depend on file-system sorting.
HALVES = [
    ("H1 2023", "2023Jan-Jun.xlsx"),
    ("H2 2023", "2023Jul-Dec.xlsx"),
    ("H1 2024", "2024Jan-Jun.xlsx"),
    ("H2 2024", "2024Jul-Dec.xlsx"),
    ("H1 2025", "2025Jan-Jun.xlsx"),
    ("H2 2025", "2025Jul-Dec.xlsx"),
    ("H1 2026", "2026Jan-Jun.xlsx"),
]
HALF_LABELS = [h for h, _ in HALVES]


def load_reports(source: Path = NETFLIX_DIR) -> pd.DataFrame:
    """Return one row per source row: half, title, hours, release_date, content_type, is_other.

    content_type is 'film' / 'series' from the sheet name, or 'unknown' for H1 2023 (single sheet).
    """
    frames = []
    for half, fname in HALVES:
        path = source / fname
        wb = openpyxl.load_workbook(path, read_only=True)
        sheets = list(wb.sheetnames)
        wb.close()
        for sh in sheets:
            loaded = load_sheet(path, sh)
            c = canonicalize(loaded["df"], sh)
            c["half"] = half
            frames.append(c[["half", "title", "hours_viewed", "release_date", "content_type", "is_other", "sheet"]])
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------------- IMDb
IMDB_FILES = {
    "title.basics.tsv.gz": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "title.ratings.tsv.gz": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    "title.akas.tsv.gz": "https://datasets.imdbws.com/title.akas.tsv.gz",
}


def _read_tsv_chunks(path: Path, usecols: list[str], chunksize: int = 1_000_000):
    """Chunked reader for IMDb TSVs.

    Why these options: IMDb uses the literal ``\\N`` for NULL, so default NA parsing is switched off
    (otherwise real titles such as "NA" or "null" would become NaN); QUOTE_NONE because titles
    contain unbalanced quote characters.
    """
    return pd.read_csv(
        path, sep="\t", usecols=usecols, dtype=str, na_values=["\\N"], keep_default_na=False,
        quoting=csv.QUOTE_NONE, chunksize=chunksize, compression="gzip",
    )


def load_basics(path: Path, wanted_types: set[str]) -> tuple[pd.DataFrame, set[str]]:
    """Return (basics restricted to wanted title types, set of ALL genre values in the file).

    The genre set is taken over the whole file because Gate 2 requires a check of every distinct
    genre value against the frozen mapping before matching.
    """
    parts, genres = [], set()
    for ch in _read_tsv_chunks(path, ["tconst", "titleType", "primaryTitle", "originalTitle", "startYear", "genres"]):
        g = ch["genres"].dropna()
        for s in g.unique():
            genres.update(s.split(","))
        parts.append(ch[ch["titleType"].isin(wanted_types)])
    df = pd.concat(parts, ignore_index=True)
    df["startYear"] = pd.to_numeric(df["startYear"], errors="coerce")
    return df, genres


def load_votes(path: Path) -> dict[str, int]:
    r = pd.read_csv(path, sep="\t", dtype={"tconst": str}, na_values=["\\N"], keep_default_na=False,
                    quoting=csv.QUOTE_NONE, compression="gzip")
    return dict(zip(r["tconst"], r["numVotes"].astype(int)))


def count_rows_and_sha(path: Path) -> tuple[int, str]:
    """Rows (excluding the header line) of a gzipped TSV and sha256 of the compressed file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    n = 0
    with gzip.open(path, "rb") as f:
        for n, _ in enumerate(f):
            pass
    return n, h.hexdigest()  # enumerate is 0-based and the first line is the header, so n = data rows


def record_imdb_manifest(manifest_path: Path, imdb_dir: Path = IMDB_DIR) -> list[dict]:
    """Add one manifest entry per IMDb file used (URL, download date, rows, sha256).

    downloaded_on is the file modification date (closest local evidence, same convention as
    the Netflix entries).
    """
    from datetime import datetime

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = {d["name"]: d for d in manifest["datasets"]}
    out = []
    for name, url in IMDB_FILES.items():
        p = imdb_dir / name
        rows, sha = count_rows_and_sha(p)
        entry = {
            "name": name,
            "file_path": f"~/Downloads/imdb-datasets/{name}",
            "source_url": url,
            "license": "IMDb Non-Commercial Datasets (personal, non-commercial use; only aggregates published)",
            "downloaded_on": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
            "row_count": rows,
            "checksum": {"algorithm": "sha256", "value": sha},
            "notes": "Stored outside the repo (read-only). row_count = data rows excluding the header line. "
                     "downloaded_on = file modification date.",
        }
        existing[name] = entry
        out.append(entry)
    manifest["datasets"] = list(existing.values())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
