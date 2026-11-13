"""Cleaning, title keys and the hours-only labelling scope (plan sections P1, P2, P4).

Every rule below was fixed in 04_analysis_plan.md before any genre share was computed.
No genre information is used in this module.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- title cleaning
# Season words in the languages that occur in Netflix's second-language segments. Used so the
# alternate (non-first) segments get the same season tail removed as the first segment.
_SEASON_WORDS = r"(?:season|temporada|saison|staffel|stagione|sezon|сезон|시즌|シーズン)"
# Tail starting at a season marker, e.g. ": Season 3", " - Season 3: subtitle", "Temporada 2".
# Why drop the subtitle too: "Squid Game: The Challenge: Season 1" and "X: Season 1: Subtitle"
# must collapse to the same base as the other seasons of the show.
RE_SEASON = re.compile(rf"\s*[:\-–]?\s*\b{_SEASON_WORDS}\s*\d+.*$", re.I)
# Part / volume / chapter / book tails need a separator so that a title that merely contains the
# word (e.g. "Book of Eli") is not cut.
RE_PART = re.compile(r"\s*[:\-–]\s*(?:part|volume|vol\.?|chapter|book)\s*\d+.*$", re.I)
RE_LIMITED = re.compile(r"\s*[:\-–]?\s*limited series\s*$", re.I)
RE_YEAR_TAG = re.compile(r"\s*\(((?:19|20)\d{2})\)\s*$")
# "Stranger Things 4": trailing 1-2 digit number after a space (series only, see below).
RE_TRAIL_NUM = re.compile(r"^(.*\S)\s+(\d{1,2})$")

LANG_SEP = " // "


@dataclass
class CleanTitle:
    """Result of cleaning one raw Netflix title string."""

    key: str                      # lowercased first segment with tags removed
    segments: list[str]           # lowercased cleaned segments (first = key)
    tag_year: int | None          # year from a trailing "(YYYY)" tag on the first segment
    tagged: bool                  # raw title contains " // " (the only language proxy)
    series_tag_stripped: bool     # a season / part / limited / trailing-number tag was removed
    trailing_number_stripped: bool = False
    base_without_trailing_number: str | None = None  # candidate base for unknown-type rows


def _collapse(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", s).strip()


def _clean_segment(seg: str, content_type: str) -> tuple[str, int | None, bool, bool, str | None]:
    """Clean one segment. Returns (text, year, series_tag_stripped, trailing_stripped, alt_base).

    Why content-type dependent: season / part / limited-series tags and trailing numbers exist
    only on series titles. Applying them to films would damage real titles ("Kill Bill: Vol. 1",
    "Fast & Furious 9"). 'unknown' (H1 2023, no sheet split) gets the explicit tags but NOT the
    trailing number; the trailing-number split is resolved later against other halves.
    """
    s = seg.strip()
    stripped = False
    if content_type in ("series", "unknown"):
        for rx in (RE_SEASON, RE_PART, RE_LIMITED):
            new = rx.sub("", s)
            if new != s and new.strip():
                s, stripped = new.strip(), True
    year = None
    m = RE_YEAR_TAG.search(s)
    if m:
        year = int(m.group(1))
        s = s[: m.start()].strip()
    trailing = False
    alt_base = None
    m2 = RE_TRAIL_NUM.match(s)
    if m2:
        if content_type == "series":
            s, trailing, stripped = m2.group(1), True, True
        elif content_type == "unknown":
            alt_base = m2.group(1)
    return s, year, stripped, trailing, alt_base


def clean_title(raw: str, content_type: str) -> CleanTitle:
    parts = [p for p in raw.split(LANG_SEP)]
    cleaned = [_clean_segment(p, content_type) for p in parts]
    text, year, stripped, trailing, alt = cleaned[0]
    segs = [_collapse(c[0]) for c in cleaned]
    return CleanTitle(
        key=segs[0], segments=segs, tag_year=year, tagged=LANG_SEP in raw,
        series_tag_stripped=stripped, trailing_number_stripped=trailing,
        base_without_trailing_number=_collapse(alt) if alt else None,
    )


# --------------------------------------------------------------------------- half-year table
@dataclass
class Cleaned:
    half_keys: pd.DataFrame       # one row per (half, key): hours, content types seen
    key_info: pd.DataFrame        # one row per key
    log: dict = field(default_factory=dict)


def clean_reports(raw: pd.DataFrame) -> Cleaned:
    """Apply P1/P2: drop invalid rows, build keys, merge duplicates by sum, build key table."""
    log: dict = {"rows_in": int(len(raw))}
    df = raw.copy()
    # "Other Movies / Other Shows" are aggregates, not titles: kept only for the 'all hours' total.
    other = df[df["is_other"]]
    log["other_rows"] = int(len(other))
    log["other_hours_by_half"] = {h: float(g["hours_viewed"].sum()) for h, g in other.groupby("half", sort=False)}
    df = df[~df["is_other"]].copy()

    # Missing / non-numeric hours: drop and count. Zero or negative hours: stop (plan P2).
    bad = df["hours_viewed"].isna() | df["title"].isna()
    log["dropped_missing_hours_or_title"] = int(bad.sum())
    df = df[~bad].copy()
    if (df["hours_viewed"] <= 0).any():
        raise SystemExit("STOP: zero or negative hours found (plan P2 requires stopping)")
    df["title"] = df["title"].astype(str)

    cts = [clean_title(t, c) for t, c in zip(df["title"], df["content_type"])]
    df["key"] = [c.key for c in cts]
    df["tag_year"] = [c.tag_year for c in cts]
    df["tagged"] = [c.tagged for c in cts]
    df["series_tag_stripped"] = [c.series_tag_stripped for c in cts]
    df["alt_base"] = [c.base_without_trailing_number for c in cts]
    df["segments"] = [c.segments for c in cts]

    # Unknown-type rows (H1 2023): strip a trailing number only if the stripped base is a key of a
    # series row elsewhere. Why: "Stranger Things 4" must merge with "Stranger Things", but a film
    # such as "Fast & Furious 9" must stay intact; other halves tell us which bases are series.
    series_keys = set(df.loc[df["content_type"] == "series", "key"])
    is_unk = (df["content_type"] == "unknown") & df["alt_base"].notna()
    hit = is_unk & df["alt_base"].isin(series_keys)
    log["unknown_rows_trailing_number_resolved"] = int(hit.sum())
    df.loc[hit, "key"] = df.loc[hit, "alt_base"]
    df.loc[hit, "series_tag_stripped"] = True
    # Rebuild the list column in one go (assigning ragged lists through .loc fails in pandas).
    df["segments"] = [[a] + sg[1:] if h else sg for a, sg, h in zip(df["alt_base"], df["segments"], hit)]

    log["duplicate_full_rows"] = int(df.duplicated(["half", "title", "hours_viewed", "release_date"]).sum())

    # Merge rows with the same key within a half by summing hours (seasons become one series).
    # Per-type hours as plain columns: vectorised and avoids slow per-group lambdas.
    df["film_hours"] = df["hours_viewed"].where(df["content_type"] == "film", 0.0)
    df["series_hours"] = df["hours_viewed"].where(df["content_type"] == "series", 0.0)
    half_keys = df.groupby(["half", "key"], sort=False).agg(
        hours=("hours_viewed", "sum"),
        n_rows=("hours_viewed", "size"),
        film_hours=("film_hours", "sum"),
        series_hours=("series_hours", "sum"),
    ).reset_index()
    log["merged_rows"] = int((half_keys["n_rows"] > 1).sum())
    log["rows_absorbed_by_merge"] = int((half_keys["n_rows"] - 1).sum())
    both = (half_keys["film_hours"] > 0) & (half_keys["series_hours"] > 0)
    log["movie_series_collisions_within_half"] = int(both.sum())

    # Key-level facts used for matching.
    df = df.sort_values("hours_viewed", ascending=False, kind="stable")
    rep = df.groupby("key", sort=False).first()  # representative row = highest-hours raw row
    ki = pd.DataFrame(index=rep.index)
    ki["rep_title"] = rep["title"]
    ki["tagged"] = rep["tagged"]
    ki["segments"] = rep["segments"]
    ki["series_tag_stripped"] = df.groupby("key")["series_tag_stripped"].any()
    ki["tag_year"] = df.dropna(subset=["tag_year"]).groupby("key")["tag_year"].first()
    ki["release_date"] = df.groupby("key")["release_date"].min()  # earliest listed date for the key
    fh = half_keys.groupby("key")[["film_hours", "series_hours"]].sum()
    ki = ki.join(fh)
    ki["type_known"] = np.where((ki["film_hours"] == 0) & (ki["series_hours"] == 0), "unknown",
                                np.where(ki["film_hours"] >= ki["series_hours"], "film", "series"))
    log["movie_series_collisions_across_halves"] = int(((ki["film_hours"] > 0) & (ki["series_hours"] > 0)).sum())
    ki.index.name = "key"
    return Cleaned(half_keys=half_keys, key_info=ki.reset_index(), log=log)


# --------------------------------------------------------------------------- scope (P4)
def scope_counts(half_keys: pd.DataFrame, targets=(0.90, 0.85, 0.80)) -> pd.DataFrame:
    """Number of keys per half needed to reach each cumulative-hours target, and the union size.

    Hours only (no genre information). Keys are sorted by hours desc, then key (deterministic
    under the many ties in the coarse hour values).
    """
    rows = []
    for t in targets:
        union: set[str] = set()
        per_half = {}
        for half, g in half_keys.groupby("half", sort=False):
            g = g.sort_values(["hours", "key"], ascending=[False, True])
            cum = g["hours"].cumsum() / g["hours"].sum()
            n = int(np.searchsorted(cum.to_numpy(), t - 1e-12) + 1)
            per_half[half] = n
            union.update(g["key"].iloc[:n])
        rows.append({"target": t, "union_keys": len(union), **{f"n_{h}": n for h, n in per_half.items()}})
    return pd.DataFrame(rows)


def scope_keys(half_keys: pd.DataFrame, target: float) -> dict[str, set[str]]:
    """Keys inside the scope for each half at a cumulative-hours target."""
    out = {}
    for half, g in half_keys.groupby("half", sort=False):
        g = g.sort_values(["hours", "key"], ascending=[False, True])
        cum = g["hours"].cumsum() / g["hours"].sum()
        n = int(np.searchsorted(cum.to_numpy(), target - 1e-12) + 1)
        out[half] = set(g["key"].iloc[:n])
    return out
