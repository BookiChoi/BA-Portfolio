"""Read-only data profile of the seven Netflix "What We Watched" engagement reports.

Scope: describe the files as they are (structure, missingness, distributions, title
overlap, season notation). No interpretation, no cleaning of the source files.

Reads the xlsx files from a source folder (default ``~/Downloads/netflix-reports``) and never
writes there. Writes only small, aggregated JSON/CSV files (plus one English markdown table
summary) into this project. No row-level data is exported.

Run from the project folder:
    ../../.venv/bin/python pipeline/profile_reports.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

import openpyxl
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("~/Downloads/netflix-reports").expanduser()
OUT_DIR = PROJECT_DIR / "outputs" / "profile"
SUMMARY_MD = PROJECT_DIR / "workflow" / "01b_data_profile.md"
MANIFEST = PROJECT_DIR / "data_manifest.json"

# Header names as they appear in the files -> canonical column names.
CANONICAL = {
    "title": "title",
    "available globally?": "available_globally",
    "release date": "release_date",
    "hours viewed": "hours_viewed",
    "runtime": "runtime",
    "views": "views",
}
# Sheet name -> content type. The split between films and series lives in the sheet name
# (sheet names changed over time). 2023 H1 has a single "Engagement" sheet with no split.
SHEET_TYPE = {"tv": "series", "shows": "series", "film": "film", "movies": "film"}
OTHER_RE = re.compile(r"^Other (Movies|Shows)$")
PLACEHOLDER = "*"  # used by Netflix for "not applicable" cells in the "Other" rows


# --------------------------------------------------------------------------- reading
def read_rows(path: Path, sheet: str) -> list[tuple]:
    """Return all rows of a sheet as tuples (read-only workbook, source is never modified)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return list(wb[sheet].iter_rows(values_only=True))
    finally:
        wb.close()


def find_header_row(rows: list[tuple], anchor: str = "Title", max_scan: int = 30) -> int:
    """Return the 0-based index of the header row.

    Why: every report starts with empty rows, a report title and a period line ("Hours viewed
    from January to June 2023") before the real header. The position is not fixed across
    files, so we locate the first row that has a cell equal to ``anchor`` instead of
    hard-coding row 6. Rows above it are skipped by the code and only recorded as metadata.
    """
    for i, row in enumerate(rows[:max_scan]):
        if any(isinstance(c, str) and c.strip() == anchor for c in row):
            return i
    raise ValueError(f"header row with {anchor!r} not found in first {max_scan} rows")


def load_sheet(path: Path, sheet: str) -> dict:
    """Load one sheet into a raw DataFrame plus bookkeeping about skipped rows."""
    rows = read_rows(path, sheet)
    h = find_header_row(rows)
    header_cells = [(i, str(c).strip()) for i, c in enumerate(rows[h]) if c is not None]
    idx = [i for i, _ in header_cells]
    raw_names = [n for _, n in header_cells]
    skipped_above = [
        " | ".join(str(c) for c in r if c is not None) for r in rows[:h] if any(c is not None for c in r)
    ]
    data, footnotes, blank = [], [], 0
    for r in rows[h + 1 :]:
        if all(c is None for c in r):
            blank += 1
            continue
        vals = [r[i] if i < len(r) else None for i in idx]
        # Footnote rows: text in the title column, every other header column empty.
        if isinstance(vals[0], str) and all(v is None for v in vals[1:]):
            footnotes.append(vals[0])
            continue
        data.append(vals)
    df = pd.DataFrame(data, columns=raw_names)
    return {
        "df": df,
        "raw_names": raw_names,
        "header_row_excel": h + 1,
        "skipped_above": skipped_above,
        "rows_blank": blank,
        "footnotes": footnotes,
    }


# --------------------------------------------------------------------------- parsing
def to_num(v):
    if isinstance(v, bool):
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    return float("nan")


def parse_runtime(v) -> float:
    """'7:34' -> 454.0 minutes; '*' or anything unparsable -> NaN."""
    if isinstance(v, str):
        m = re.fullmatch(r"(\d+):(\d{2})(?::(\d{2}))?", v.strip())
        if m:
            return int(m[1]) * 60 + int(m[2]) + (int(m[3]) / 60 if m[3] else 0)
    return float("nan")


def parse_date(v):
    """Dates come as datetime objects (2023 H1) or ISO strings (later files)."""
    if isinstance(v, (datetime, date)):
        return pd.Timestamp(v)
    if isinstance(v, str) and v.strip() != PLACEHOLDER:
        return pd.to_datetime(v.strip(), errors="coerce", format="%Y-%m-%d")
    return pd.NaT


def canonicalize(df: pd.DataFrame, sheet: str) -> pd.DataFrame:
    """Add canonical, parsed columns while keeping the raw ones (prefix ``raw_``)."""
    out = pd.DataFrame(index=df.index)
    for col in df.columns:
        key = CANONICAL.get(col.strip().lower())
        if key:
            out["raw_" + key] = df[col]
    for key in CANONICAL.values():
        if "raw_" + key not in out.columns:  # column absent in this sheet (e.g. Runtime in 2023 H1)
            out["raw_" + key] = pd.Series([None] * len(df), index=df.index, dtype=object)
    out["title"] = out["raw_title"]
    out["is_other"] = out["title"].map(lambda t: bool(isinstance(t, str) and OTHER_RE.match(t)))
    out["hours_viewed"] = out["raw_hours_viewed"].map(to_num)
    out["views"] = out["raw_views"].map(to_num)
    out["runtime_minutes"] = out["raw_runtime"].map(parse_runtime)
    out["release_date"] = out["raw_release_date"].map(parse_date)
    out["content_type"] = SHEET_TYPE.get(sheet.strip().lower(), "unknown")
    out["sheet"] = sheet
    return out


# --------------------------------------------------------------------------- profiling
def describe(s: pd.Series) -> dict:
    s = s.dropna()
    if s.empty:
        return {"count": 0}
    q = s.quantile([0.25, 0.5, 0.75, 0.9, 0.99])
    return {
        "count": int(s.size),
        "min": float(s.min()),
        "p25": float(q[0.25]),
        "median": float(q[0.5]),
        "mean": float(s.mean()),
        "p75": float(q[0.75]),
        "p90": float(q[0.9]),
        "p99": float(q[0.99]),
        "max": float(s.max()),
    }


def outliers(df: pd.DataFrame, col: str) -> dict:
    s = df[col].dropna()
    if s.empty:
        return {"count_above_fence": 0}
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    fence = float(q3 + 1.5 * (q3 - q1))
    top = df.loc[~df["is_other"]].nlargest(5, col)[["title", col]]
    return {
        "iqr_upper_fence": fence,
        "count_above_fence": int((s > fence).sum()),
        "top5": [{"title": t, "value": float(v)} for t, v in zip(top["title"], top[col])],
    }


def profile_frame(df: pd.DataFrame, header_names: list[str]) -> dict:
    """Profile one frame (a sheet, or all sheets of a file stacked)."""
    title_rows = df.loc[~df["is_other"]]
    n_title_rows = len(title_rows)
    header_set = {h.casefold() for h in header_names}

    present = {CANONICAL.get(h.strip().lower()) for h in header_names}
    cols = {}
    for key in CANONICAL.values():
        raw = df["raw_" + key]
        non_null = raw.notna()
        n_placeholder = int(raw.map(lambda v: v == PLACEHOLDER).sum())
        header_phrase = int(raw.map(lambda v: isinstance(v, str) and v.strip().casefold() in header_set).sum())
        cols[key] = {
            "column_present": key in present,
            "non_null": int(non_null.sum()),
            "missing": int((~non_null).sum()),
            "missing_pct": round(float((~non_null).mean() * 100), 4) if len(df) else None,
            "distinct": int(raw[non_null].astype(str).nunique()),
            "duplicate_values": int(non_null.sum() - raw[non_null].astype(str).nunique()),
            "placeholder_star": n_placeholder,
            "header_phrase_rows": header_phrase,
        }
    full_dups = int(df[[c for c in df.columns if c.startswith("raw_")]].astype(str).duplicated().sum())
    header_phrase_rows = int(
        df[[f"raw_{k}" for k in CANONICAL.values()]]
        .apply(lambda col: col.map(lambda v: isinstance(v, str) and v.strip().casefold() in header_set))
        .any(axis=1)
        .sum()
    )

    hours_all = float(df["hours_viewed"].sum())
    hours_title = float(title_rows["hours_viewed"].sum())
    top10 = title_rows.nlargest(10, "hours_viewed")["hours_viewed"].sum()

    rel = title_rows["release_date"]
    rel_raw = title_rows["raw_release_date"]
    release = {
        "rows_considered": n_title_rows,
        "missing": int(rel_raw.isna().sum()),
        "missing_pct": round(float(rel_raw.isna().mean() * 100), 4) if n_title_rows else None,
        "placeholder_star": int((rel_raw == PLACEHOLDER).sum()),
        "unparsable": int((rel.isna() & rel_raw.notna() & (rel_raw != PLACEHOLDER)).sum()),
        "min": rel.min().strftime("%Y-%m-%d") if rel.notna().any() else None,
        "max": rel.max().strftime("%Y-%m-%d") if rel.notna().any() else None,
    }
    avail = df["raw_available_globally"].map(lambda v: "<missing>" if v is None or pd.isna(v) else str(v))
    avail_counts = avail.value_counts()
    available = {k: {"count": int(v), "pct": round(float(v / len(df) * 100), 4)} for k, v in avail_counts.items()}

    return {
        "rows_data": int(len(df)),
        "rows_other": int(df["is_other"].sum()),
        "rows_title_level": n_title_rows,
        "distinct_titles": int(title_rows["title"].nunique()),
        "rows_by_content_type": {k: int(v) for k, v in df["content_type"].value_counts().items()},
        "columns": cols,
        "duplicate_full_rows": full_dups,
        "rows_with_header_phrase": header_phrase_rows,
        "hours": {
            "total_incl_other": hours_all,
            "total_title_level": hours_title,
            "top10_hours": float(top10),
            "top10_share_of_total_incl_other": float(top10 / hours_all) if hours_all else None,
            "top10_share_of_title_level": float(top10 / hours_title) if hours_title else None,
        },
        "numeric": {
            "hours_viewed": describe(df["hours_viewed"]),
            "runtime_minutes": describe(df["runtime_minutes"]),
            "views": describe(df["views"]),
        },
        "outliers": {c: outliers(df, c) for c in ("hours_viewed", "views", "runtime_minutes")},
        "release_date": release,
        "available_globally": available,
    }


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def profile_file(path: Path) -> tuple[dict, pd.DataFrame, dict]:
    """Return (profile dict, stacked canonical frame, structure info)."""
    wb = openpyxl.load_workbook(path, read_only=True)
    sheets = list(wb.sheetnames)
    wb.close()
    frames, sheet_profiles, structure = [], [], []
    for sh in sheets:
        loaded = load_sheet(path, sh)
        cdf = canonicalize(loaded["df"], sh)
        frames.append(cdf)
        p = profile_frame(cdf, loaded["raw_names"])
        p.update(
            {
                "sheet": sh,
                "content_type": SHEET_TYPE.get(sh.strip().lower(), "unknown"),
                "header_row_excel": loaded["header_row_excel"],
                "skipped_rows_above_header": loaded["skipped_above"],
                "header_columns": loaded["raw_names"],
                "rows_blank": loaded["rows_blank"],
                "rows_footnote": len(loaded["footnotes"]),
                "footnotes": loaded["footnotes"],
            }
        )
        sheet_profiles.append(p)
        structure.append({"sheet": sh, "header_row_excel": loaded["header_row_excel"], "columns": loaded["raw_names"]})
    all_df = pd.concat(frames, ignore_index=True)
    names = sorted({n for s in structure for n in s["columns"]})
    total = profile_frame(all_df, names)
    n_rows_manifest = sum(s["rows_data"] for s in sheet_profiles)
    split_source = (
        "sheet name" if len({s["content_type"] for s in sheet_profiles} - {"unknown"}) >= 2 else "none (single sheet, no type column)"
    )
    prof = {
        "file": path.name,
        "sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
        "sheets": sheets,
        "content_type_split_source": split_source,
        "data_rows_all_sheets": n_rows_manifest,
        "file_total": total,
        "per_sheet": sheet_profiles,
    }
    return prof, all_df, {"structure": structure}


# --------------------------------------------------------------------------- comparisons
def column_comparison(structs: dict[str, list[dict]], reference: tuple[str, str]) -> pd.DataFrame:
    ref_file, ref_sheet = reference
    ref_cols = next(s["columns"] for s in structs[ref_file] if s["sheet"] == ref_sheet)
    all_cols = list(dict.fromkeys(c for f in structs.values() for s in f for c in s["columns"]))
    rows = []
    for fname, sheets in structs.items():
        for s in sheets:
            row = {
                "file": fname,
                "sheet": s["sheet"],
                "header_row_excel": s["header_row_excel"],
                "n_columns": len(s["columns"]),
                "columns_in_order": " | ".join(s["columns"]),
                "same_as_reference": s["columns"] == ref_cols,
                "reference": f"{ref_file}:{ref_sheet}",
            }
            for c in all_cols:
                row[f"has[{c}]"] = c in s["columns"]
            rows.append(row)
    return pd.DataFrame(rows)


def norm1(t: str) -> str:
    """Case/punctuation/width-insensitive key."""
    s = unicodedata.normalize("NFKC", t).casefold()
    return re.sub(r"[\W_]+", " ", s).strip()


def norm2(t: str) -> str:
    """norm1 of the first segment before ' // ' (bilingual titles)."""
    return norm1(t.split(" // ")[0])


def title_table(df: pd.DataFrame) -> pd.DataFrame:
    t = df.loc[~df["is_other"] & df["title"].notna(), ["title", "hours_viewed"]]
    return t.groupby("title", as_index=False)["hours_viewed"].sum()


def overlap_tables(frames: dict[str, pd.DataFrame], order: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, variants = [], []
    for a, b in zip(order[:-1], order[1:]):
        ta, tb = title_table(frames[a]), title_table(frames[b])
        sets = {"exact": (set(ta["title"]), set(tb["title"]))}
        for name, fn in (("normalized", norm1), ("normalized_first_segment", norm2)):
            sets[name] = ({fn(t) for t in ta["title"]}, {fn(t) for t in tb["title"]})
        for level, (sa, sb) in sets.items():
            m = len(sa & sb)
            rows.append(
                {
                    "earlier": a, "later": b, "match_level": level,
                    "n_earlier": len(sa), "n_later": len(sb), "n_matched": m,
                    "pct_of_earlier": round(m / len(sa) * 100, 4) if sa else None,
                    "pct_of_later": round(m / len(sb) * 100, 4) if sb else None,
                }
            )
        # Titles that match after normalisation but are spelled differently.
        ka = {t: (norm1(t), norm2(t), h) for t, h in zip(ta["title"], ta["hours_viewed"])}
        kb = {t: (norm1(t), norm2(t), h) for t, h in zip(tb["title"], tb["hours_viewed"])}
        exact = set(ta["title"]) & set(tb["title"])
        by1_a = {v[0]: t for t, v in ka.items() if t not in exact}
        by2_a = {v[1]: t for t, v in ka.items() if t not in exact}
        for tt, (n1, n2, h) in sorted(kb.items(), key=lambda kv: -kv[1][2]):
            if tt in exact:
                continue
            if n1 in by1_a:
                level, ta_title = "normalized", by1_a[n1]
            elif n2 in by2_a:
                level, ta_title = "normalized_first_segment", by2_a[n2]
            else:
                continue
            variants.append(
                {"earlier": a, "later": b, "match_level": level, "title_earlier": ta_title,
                 "title_later": tt, "hours_earlier": float(ka[ta_title][2]), "hours_later": float(h)}
            )
    vdf = pd.DataFrame(variants)
    # 10 examples: round-robin over the pairs, highest later-hours first inside each pair.
    picked, per_pair = [], {}
    if not vdf.empty:
        for pair, g in vdf.groupby(["earlier", "later"], sort=False):
            per_pair[pair] = g.sort_values("hours_later", ascending=False).to_dict("records")
        while len(picked) < 10 and any(per_pair.values()):
            for pair in list(per_pair):
                if per_pair[pair] and len(picked) < 10:
                    picked.append(per_pair[pair].pop(0))
    return pd.DataFrame(rows), pd.DataFrame(picked)


SEASON_PATTERNS = [
    ("Season N", re.compile(r"^Season \d+$")),
    ("Season N: subtitle", re.compile(r"^Season \d+: .+")),
    ("Limited Series", re.compile(r"^Limited Series$")),
    ("Part/Volume/Book N", re.compile(r"^(Part|Volume|Vol\.?|Chapter|Book) \d+", re.I)),
]


def split_notation(title: str) -> tuple[str, str]:
    """Split 'Bridgerton: Season 3' into ('Bridgerton', 'Season 3').

    Only the first language segment (before ' // ') is used. Titles without ': ' that end in a
    number ('Stranger Things 5') are split on the trailing number.
    """
    main = title.split(" // ")[0].strip()
    if ": " in main:
        base, rem = main.split(": ", 1)
        return base.strip(), rem.strip()
    m = re.fullmatch(r"(.*\S)\s+(\d+)", main)
    if m:
        return m[1], m[2]
    return main, ""


def classify_notation(rem: str, title: str) -> str:
    if rem == "":
        return "none"
    for name, rx in SEASON_PATTERNS:
        if rx.match(rem):
            return name
    if re.fullmatch(r"\d+", rem) and ": " not in title.split(" // ")[0]:
        return "trailing number"
    return "other"


def season_tables(frames: dict[str, pd.DataFrame], order: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    pat_rows, recs = [], []
    for f in order:
        df = frames[f]
        s = df.loc[~df["is_other"] & df["title"].notna() & df["content_type"].isin(["series", "unknown"])]
        counts: dict[str, int] = {}
        for t, h, ct in zip(s["title"], s["hours_viewed"], s["content_type"]):
            base, rem = split_notation(t)
            cls = classify_notation(rem, t)
            counts[cls] = counts.get(cls, 0) + 1
            recs.append({"file": f, "base": base, "full_title": t, "notation": rem, "pattern": cls,
                         "hours_viewed": h, "content_type": ct})
        n_dbl = int(s["title"].map(lambda t: " // " in t).sum())
        for cls, n in sorted(counts.items()):
            pat_rows.append({"file": f, "pattern": cls, "n_titles": n})
        pat_rows.append({"file": f, "pattern": "contains ' // ' (second-language segment)", "n_titles": n_dbl})
        pat_rows.append({"file": f, "pattern": "all series-or-unknown title rows", "n_titles": int(len(s))})
    allr = pd.DataFrame(recs)
    # Bases that appear in >= 2 files and carry a season-like notation in at least one of them.
    seasonal = allr[allr["pattern"] != "none"]
    seasonal = seasonal[seasonal["pattern"] != "other"]
    cand = []
    for base, g in allr.groupby("base"):
        if g["file"].nunique() >= 2 and base in set(seasonal["base"]):
            cand.append((base, float(g["hours_viewed"].sum())))
    cand.sort(key=lambda x: -x[1])
    keep = [b for b, _ in cand[:8]]
    ex = allr[allr["base"].isin(keep)].copy()
    ex["file"] = pd.Categorical(ex["file"], categories=order, ordered=True)
    ex["base"] = pd.Categorical(ex["base"], categories=keep, ordered=True)
    ex = ex.sort_values(["base", "file", "hours_viewed"], ascending=[True, True, False])
    ex = ex.groupby(["base", "file"], observed=True).head(2)  # top-2 titles by hours per base and file
    ex = ex.drop(columns=["content_type"])
    return pd.DataFrame(pat_rows), ex.reset_index(drop=True)


# --------------------------------------------------------------------------- outputs
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, float) and o != o:
        return None
    if hasattr(o, "item"):
        return clean(o.item())
    return o


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(clean(obj), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_manifest(profiles: list[dict], source: Path) -> None:
    """Merge one entry per source file into data_manifest.json (entry_template format).

    file_path points to the external read-only folder because the raw files must not live in
    the repo. source_url stays empty on purpose (the owner fills it in). downloaded_on is the
    file modification date, which is the closest evidence available locally.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    template = manifest["entry_template"]
    existing = {d["name"]: d for d in manifest.get("datasets", [])}
    for p in profiles:
        path = source / p["file"]
        entry = json.loads(json.dumps(template))
        entry.update(
            {
                "name": p["file"],
                "file_path": f"~/Downloads/netflix-reports/{p['file']}",
                "source_url": "",
                "license": "",
                "downloaded_on": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d"),
                "row_count": p["data_rows_all_sheets"],
                "checksum": {"algorithm": "sha256", "value": p["sha256"]},
                "notes": (
                    "Stored outside the repo (read-only). row_count = non-empty data rows below the header "
                    "on all sheets, including the 'Other Movies/Other Shows' rows, excluding blank and "
                    "footnote rows. downloaded_on = file modification date."
                ),
            }
        )
        if p["file"] in existing:
            for k in ("source_url", "license"):  # never overwrite values the owner already filled
                entry[k] = existing[p["file"]].get(k, entry[k]) or entry[k]
        existing[p["file"]] = entry
    manifest["datasets"] = list(existing.values())
    write_json(MANIFEST, manifest)


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                v = "" if v != v else (f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}")
            elif isinstance(v, (int,)) and not isinstance(v, bool):
                v = f"{v:,}"
            cells.append(str(v).replace("|", "\\|"))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def build_markdown(profiles: list[dict], comp: pd.DataFrame, overlap: pd.DataFrame, variants: pd.DataFrame,
                   patterns: pd.DataFrame, examples: pd.DataFrame) -> str:
    L = ["Author: ai/main-session", "Status: draft", "",
         "# 01b Data profile: Netflix What We Watched reports (7 files)", "",
         "Numbers only, produced by `pipeline/profile_reports.py`. Machine-readable versions are in `outputs/profile/`.",
         "Definitions: *title-level rows* exclude the `Other Movies` / `Other Shows` rows. *Top-10 share* is the hours of "
         "the 10 largest title-level rows divided by the stated total. Percentiles use linear interpolation.", ""]

    rows = []
    for p in profiles:
        t = p["file_total"]
        ct = t["rows_by_content_type"]
        rows.append({
            "file": p["file"], "sheets": ", ".join(p["sheets"]), "type split by": p["content_type_split_source"],
            "data rows": t["rows_data"], "title-level rows": t["rows_title_level"], "distinct titles": t["distinct_titles"],
            "film rows": ct.get("film", 0), "series rows": ct.get("series", 0), "unknown-type rows": ct.get("unknown", 0),
            "Other rows": t["rows_other"],
        })
    L += ["## 1. Size and structure", md_table(pd.DataFrame(rows)), ""]

    rows = []
    for p in profiles:
        for s in p["per_sheet"]:
            rows.append({"file": p["file"], "sheet": s["sheet"], "header row (Excel)": s["header_row_excel"],
                         "rows above header (non-empty)": len(s["skipped_rows_above_header"]),
                         "blank rows below": s["rows_blank"], "footnote rows": s["rows_footnote"],
                         "data rows": s["rows_data"]})
    L += ["## 2. Header position and skipped rows", md_table(pd.DataFrame(rows)), ""]

    rows = []
    for p in profiles:
        t = p["file_total"]["hours"]
        rows.append({"file": p["file"], "total hours (incl. Other)": t["total_incl_other"],
                     "total hours (title-level)": t["total_title_level"],
                     "top-10 hours": t["top10_hours"],
                     "top-10 share of total incl. Other (%)": (t["top10_share_of_total_incl_other"] or 0) * 100,
                     "top-10 share of title-level total (%)": (t["top10_share_of_title_level"] or 0) * 100})
    L += ["## 3. Total hours and top-10 concentration", md_table(pd.DataFrame(rows)), ""]

    rows = []
    for p in profiles:
        t = p["file_total"]
        for m in ("hours_viewed", "runtime_minutes", "views"):
            d = t["numeric"][m]
            if d.get("count"):
                rows.append({"file": p["file"], "metric": m, "n": d["count"], "min": d["min"], "p25": d["p25"],
                             "median": d["median"], "mean": d["mean"], "p75": d["p75"], "p90": d["p90"],
                             "p99": d["p99"], "max": d["max"]})
            else:
                rows.append({"file": p["file"], "metric": m, "n": 0})
    L += ["## 4. Distributions (all sheets of a file stacked; Other rows included where numeric)",
          md_table(pd.DataFrame(rows).fillna("")), ""]

    rows = []
    for p in profiles:
        t = p["file_total"]
        for m, d in t["outliers"].items():
            if "iqr_upper_fence" in d:
                rows.append({"file": p["file"], "metric": m, "IQR upper fence": d["iqr_upper_fence"],
                             "rows above fence": d["count_above_fence"],
                             "largest title-level value": d["top5"][0]["value"] if d["top5"] else ""})
    L += ["## 5. Outliers (Tukey fence: Q3 + 1.5 x IQR)", md_table(pd.DataFrame(rows)), ""]

    rows = []
    for p in profiles:
        t = p["file_total"]
        r = t["release_date"]
        row = {"file": p["file"], "release date missing (n)": r["missing"], "release date missing (%)": r["missing_pct"],
               "release date min": r["min"], "release date max": r["max"], "unparsable dates": r["unparsable"]}
        for key in ("available_globally",):
            for val, d in sorted(t[key].items()):
                row[f"global={val} (%)"] = d["pct"]
        rows.append(row)
    L += ["## 6. Release date and global availability", md_table(pd.DataFrame(rows).fillna("")), ""]

    rows = []
    for p in profiles:
        t = p["file_total"]
        for k, c in t["columns"].items():
            rows.append({"file": p["file"], "column": k, "missing (n)": c["missing"], "missing (%)": c["missing_pct"],
                         "column in header": c["column_present"],
                         "distinct": c["distinct"], "duplicate values": c["duplicate_values"],
                         "'*' placeholders": c["placeholder_star"], "header-phrase rows": c["header_phrase_rows"]})
        rows.append({"file": p["file"], "column": "(whole row)", "duplicate values": t["duplicate_full_rows"],
                     "header-phrase rows": t["rows_with_header_phrase"]})
    L += ["## 7. Per-column missingness, duplicates, header phrases in data rows",
          md_table(pd.DataFrame(rows).fillna("")), ""]

    cc = comp[["file", "sheet", "header_row_excel", "n_columns", "same_as_reference", "columns_in_order"]]
    L += ["## 8. Column structure comparison", f"Reference: `{comp['reference'].iloc[0]}`.", md_table(cc), ""]

    ov = overlap.copy()
    L += ["## 9. Title overlap between adjacent half-years",
          "`exact` = identical string; `normalized` = NFKC, case-folded, punctuation and spacing removed; "
          "`normalized_first_segment` = same, using the part before ` // `.", md_table(ov), ""]
    L += ["### Spelling variants (10 examples, matched after normalisation but not identical)",
          md_table(variants) if not variants.empty else "(none)", ""]

    L += ["## 10. Season notation", "Counts of series-or-unknown title rows by notation pattern.",
          md_table(patterns), "", "### Examples across half-years (8 highest-hours series bases, top 2 titles per file)",
          md_table(examples[["base", "file", "full_title", "notation", "pattern", "hours_viewed"]]), ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = ap.parse_args()
    source = args.source.expanduser()
    files = sorted(source.glob("*.xlsx"), key=lambda p: (p.name[:4], 0 if "Jan" in p.name else 1))
    if not files:
        raise SystemExit(f"no xlsx files in {source}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profiles, frames, structs = [], {}, {}
    for f in files:
        prof, df, info = profile_file(f)
        profiles.append(prof)
        frames[f.name] = df
        structs[f.name] = info["structure"]
        write_json(OUT_DIR / f"profile_{f.stem}.json", prof)

    order = [f.name for f in files]
    ref_file = order[-1]
    ref_sheet = structs[ref_file][0]["sheet"]
    comp = column_comparison(structs, (ref_file, ref_sheet))
    comp.to_csv(OUT_DIR / "column_comparison.csv", index=False)
    overlap, variants = overlap_tables(frames, order)
    overlap.to_csv(OUT_DIR / "title_overlap.csv", index=False)
    variants.to_csv(OUT_DIR / "title_variants.csv", index=False)
    patterns, examples = season_tables(frames, order)
    patterns.to_csv(OUT_DIR / "season_notation_patterns.csv", index=False)
    examples.to_csv(OUT_DIR / "season_notation_examples.csv", index=False)

    update_manifest(profiles, source)
    SUMMARY_MD.write_text(build_markdown(profiles, comp, overlap, variants, patterns, examples), encoding="utf-8")
    print(f"profiled {len(files)} files -> {OUT_DIR}")


if __name__ == "__main__":
    main()
