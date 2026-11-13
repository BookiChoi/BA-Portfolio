"""IMDb matching and genre grouping (plan section P3, frozen before the pilot).

Rules, in order (see 04_analysis_plan.md P3 and the Gate 2 year-hint rule):
 1. Normalise both sides the same way.
 2. Stage 1: normalised primaryTitle / originalTitle equals the key. Stage 2 (only for keys with no
    stage 1 candidate after filters): normalised akas title equals the key. Segment order: first
    segment, then the other segments of a tagged title. Reading of the plan used here: stage 1 over
    all segments is tried before stage 2 (stage 2 is "only for keys with no stage 1 candidate").
 3. Type filter. 4. Year filter. 5. Tie-break: most votes, then lowest numeric tconst.
 6. Genres go through the frozen priority table (config/genre_mapping.csv).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.load import _read_tsv_chunks

FILM_TYPES = {"movie", "tvMovie", "tvSpecial"}
SERIES_TYPES = {"tvSeries", "tvMiniSeries"}
ALL_TYPES = FILM_TYPES | SERIES_TYPES

_PUNCT = re.compile(r"[^\w\s]|_", re.U)
_SPACE = re.compile(r"\s+")


def norm_title(s: str) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces.

    Apostrophes are deleted (not replaced by a space) so "Grey's" and "Greys" agree. The same
    function is applied to Netflix keys and IMDb titles, which is all that matters for equality.
    """
    if not s:
        return ""
    s = s.replace("'", "").replace("’", "")
    if not s.isascii():
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        s = unicodedata.normalize("NFKC", s)
    s = _PUNCT.sub(" ", s.casefold())
    return _SPACE.sub(" ", s).strip()


# --------------------------------------------------------------------------- mapping
def load_mapping(path: Path) -> pd.DataFrame:
    m = pd.read_csv(path, dtype={"imdb_genre": str, "group": str}, keep_default_na=False)
    m["group_priority"] = pd.to_numeric(m["group_priority"].replace("", np.nan), errors="coerce")
    return m


def check_genres_covered(genres: set[str], mapping: pd.DataFrame) -> list[str]:
    """Return genre values found in title.basics but absent from the mapping (stop if non-empty)."""
    return sorted(g for g in genres if g not in set(mapping["imdb_genre"]))


def genre_group(genres: str | float, mapping: pd.DataFrame) -> str | None:
    """Group with the smallest priority among the title's mappable genres, else None."""
    if not isinstance(genres, str):
        return None
    lookup = _lookup(mapping)
    best = None
    for g in genres.split(","):
        hit = lookup.get(g)
        if hit and (best is None or hit[1] < best[1]):
            best = hit
    return best[0] if best else None


_LOOKUP_CACHE: dict[int, dict] = {}


def _lookup(mapping: pd.DataFrame) -> dict:
    k = id(mapping)
    if k not in _LOOKUP_CACHE:
        mm = mapping[(mapping["group"] != "") & mapping["group_priority"].notna()]
        _LOOKUP_CACHE[k] = {r.imdb_genre: (r.group, float(r.group_priority)) for r in mm.itertuples()}
    return _LOOKUP_CACHE[k]


# --------------------------------------------------------------------------- index
class ImdbIndex:
    """Normalised-title index over title.basics (restricted to the allowed title types)."""

    def __init__(self, basics: pd.DataFrame, votes: dict[str, int], needed_norms: set[str]):
        self.votes = votes
        b = basics.reset_index(drop=True)
        self.b = b
        prim = b["primaryTitle"].fillna("").map(norm_title)
        orig = b["originalTitle"].fillna("").map(norm_title)
        self.by_norm: dict[str, list[int]] = {}
        for col in (prim, orig):
            mask = col.isin(needed_norms)
            for i, n in zip(np.flatnonzero(mask.to_numpy()), col[mask]):
                lst = self.by_norm.setdefault(n, [])
                if int(i) not in lst:  # primary and original title may both match the same row
                    lst.append(int(i))
        self.pos_of = {t: i for i, t in enumerate(b["tconst"])}
        self.akas_by_norm: dict[str, list[int]] = {}

    def add_akas(self, akas_path: Path, needed_norms: set[str]) -> int:
        """Load akas titles equal (after normalisation) to a needed key; map them to basics rows."""
        valid = self.pos_of
        n_hits = 0
        for ch in _read_tsv_chunks(akas_path, ["titleId", "title"], chunksize=2_000_000):
            ch = ch[ch["titleId"].isin(valid)]
            norms = [norm_title(t) for t in ch["title"].tolist()]
            for tid, n in zip(ch["titleId"].tolist(), norms):
                if n in needed_norms:
                    lst = self.akas_by_norm.setdefault(n, [])
                    p = valid[tid]
                    if p not in lst:
                        lst.append(p)
                        n_hits += 1
        return n_hits

    # ------------------------------------------------------------------ matching
    def _filter(self, idx: list[int], allowed: set[str], year_rule: str, ref_year: int | None):
        b = self.b
        out = []
        for i in idx:
            t = b.at[i, "titleType"]
            if t not in allowed:
                continue
            sy = b.at[i, "startYear"]
            if year_rule != "none" and ref_year is not None:
                if pd.isna(sy):
                    continue
                if year_rule == "film_pm1" and abs(sy - ref_year) > 1:
                    continue
                if year_rule == "series_le" and sy > ref_year + 1:
                    continue
            out.append(i)
        return out

    def match(self, segments: list[str], key_type: str, series_tag_stripped: bool,
              release_year: int | None, tag_year: int | None) -> dict:
        """Return a dict describing the match for one key (or an unmatched record).

        Year rule precedence: release date (P3 rule 4) if present, else the year tag (Gate 2).
        Type rule: H1 2023-only keys ('unknown') are treated as series if a series tag was stripped,
        otherwise all five types are allowed.
        """
        if key_type == "film":
            allowed, type_rule = FILM_TYPES, "film"
        elif key_type == "series":
            allowed, type_rule = SERIES_TYPES, "series"
        elif series_tag_stripped:
            allowed, type_rule = SERIES_TYPES, "unknown->series(tag)"
        else:
            allowed, type_rule = ALL_TYPES, "unknown->all"
        if release_year is not None:
            year_src, ref = "release_date", release_year
        elif tag_year is not None:
            year_src, ref = "tag_year", tag_year
        else:
            year_src, ref = "none", None

        norms = [norm_title(s) for s in segments]
        # Gate 2 amendment 1: stage 1 (basics) over ALL segments; only if no segment gives a
        # candidate after the filters does stage 2 (akas) run. Candidates are pooled across segments;
        # a candidate found by more than one segment is preferred, then votes, then lowest tconst.
        for stage, table in (("stage1", self.by_norm), ("stage2_akas", self.akas_by_norm)):
            seg_hits: dict[int, set[int]] = {}   # candidate row -> segment numbers that found it
            for si, n in enumerate(norms):
                cand = table.get(n, []) if n else []
                if not cand:
                    continue
                if year_src == "none":
                    rule = "none"
                elif allowed is FILM_TYPES or year_src == "tag_year":
                    rule = "film_pm1"  # |diff|<=1 (films, and any type when the hint is a year tag)
                elif allowed is SERIES_TYPES:
                    rule = "series_le"  # series start <= release year + 1 (release-date rule)
                else:
                    rule = "mixed"
                if rule == "mixed":
                    f = self._filter(cand, FILM_TYPES, "film_pm1", ref) + self._filter(cand, SERIES_TYPES, "series_le", ref)
                else:
                    f = self._filter(cand, allowed, rule, ref)
                for i in f:
                    seg_hits.setdefault(i, set()).add(si + 1)
            if not seg_hits:
                continue
            ranked = sorted(seg_hits, key=lambda i: (-len(seg_hits[i]), -self.votes.get(self.b.at[i, "tconst"], 0),
                                                     int(self.b.at[i, "tconst"][2:])))
            top = ranked[0]
            tv = self.votes.get(self.b.at[top, "tconst"], 0)
            if len(ranked) == 1:
                tb = "none"
            elif len(seg_hits[ranked[1]]) < len(seg_hits[top]):
                tb = "multi_segment"
            elif self.votes.get(self.b.at[ranked[1], "tconst"], 0) < tv:
                tb = "votes"
            else:
                tb = "tconst"
            row = self.b.loc[top]
            return {
                "matched": True, "tconst": row["tconst"], "imdb_title": row["primaryTitle"],
                "imdb_type": row["titleType"], "imdb_year": row["startYear"], "imdb_genres": row["genres"],
                "stage": stage, "segments_matched": ",".join(map(str, sorted(seg_hits[top]))),
                "candidates_after_filter": len(ranked), "tie_break": tb,
                "type_rule": type_rule, "year_source": year_src,
            }
        return {"matched": False, "tconst": None, "imdb_title": None, "imdb_type": None, "imdb_year": np.nan,
                "imdb_genres": None, "stage": None, "segments_matched": None, "candidates_after_filter": 0,
                "tie_break": None, "type_rule": type_rule, "year_source": year_src}
