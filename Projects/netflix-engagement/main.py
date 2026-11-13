"""Entry point for the Netflix engagement project (Q1: does any genre alternate by half-year?).

Stages (run from the project folder, ``MPLBACKEND=Agg``):
    python main.py manifest   # record IMDb files in data_manifest.json (URL, date, rows, sha256)
    python main.py pilot      # clean, scope (P4), pilot match on 30 keys (P5), then STOP
    python main.py full       # full-scope labelling + Q1 checks, bootstrap, permutation, charts
``full`` refuses to run unless workflow/05_pilot_check.md exists (Gate 2: the human's pilot check).
Set Q1_CACHE=<dir outside the repo> to cache the key-level label table between runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import clean, label, load
from pipeline.q1_run import stage_full

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "q1"
SEED = 42
PILOT_GATE = 0.85
MAX_KEYS = 4500  # Gate 2 amendment 1: raised from 3,000 (local IMDb files, compute-only cost)


def stage_manifest() -> None:
    for e in load.record_imdb_manifest(ROOT / "data_manifest.json"):
        print(e["name"], "rows", e["row_count"], "sha256", e["checksum"]["value"], "date", e["downloaded_on"])


def stage_pilot() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # ---- P1/P2
    raw = load.load_reports()
    cl = clean.clean_reports(raw)
    print("CLEAN LOG", json.dumps(cl.log, indent=2, default=str))
    (OUT / "clean_log.json").write_text(json.dumps(cl.log, indent=2, default=str) + "\n")

    # ---- P4 scope (hours only)
    cl.collisions.to_csv(OUT / "collisions_top20.csv", index=False)
    print("TOP 20 TITLE-ONLY MOVIE/SHOW COLLISIONS\n", cl.collisions.to_string())
    sc = clean.scope_counts(cl.half_keys, id_col="kid")
    print("SCOPE CANDIDATES\n", sc.to_string())
    sc.to_csv(OUT / "scope_candidates.csv", index=False)
    chosen = None
    for t in (0.90, 0.85, 0.80):
        if int(sc.loc[np.isclose(sc["target"], t), "union_keys"].iloc[0]) <= MAX_KEYS:
            chosen = t
            break
    if chosen is None:
        print("STOP: even the 80% target exceeds", MAX_KEYS, "unique keys; ask the human (plan P4).")
        sys.exit(3)
    in_scope = clean.scope_keys(cl.half_keys, chosen, id_col="kid")
    union = sorted(set().union(*in_scope.values()))
    print(f"CHOSEN TARGET {chosen:.0%}; union keys {len(union)}")
    json.dump({"target": chosen, "union_keys": len(union),
               "keys_per_half": {h: len(k) for h, k in in_scope.items()}},
              open(OUT / "scope.json", "w"), indent=2)

    # ---- P5 pilot sample: 15 tagged + 15 untagged, seed 42
    ki = cl.key_info.set_index("kid")
    cand = ki.loc[union]
    rng = np.random.default_rng(SEED)
    pick = []
    for flag in (True, False):
        pool = sorted(cand.index[cand["tagged"] == flag])
        pick += list(rng.choice(pool, size=15, replace=False))
    print("pool sizes tagged/untagged:", int(cand["tagged"].sum()), int((~cand["tagged"]).sum()))

    # ---- genre mapping check (stop if any IMDb genre is unmapped)
    mapping = label.load_mapping(ROOT / "config" / "genre_mapping.csv")
    basics, genres = load.load_basics(load.IMDB_DIR / "title.basics.tsv.gz", label.ALL_TYPES)
    missing = label.check_genres_covered(genres, mapping)
    print("DISTINCT GENRES IN title.basics:", len(genres), sorted(genres))
    if missing:
        print("STOP: genres missing from mapping:", missing)
        sys.exit(4)
    votes = load.load_votes(load.IMDB_DIR / "title.ratings.tsv.gz")

    needed = {label.norm_title(s) for k in pick for s in ki.at[k, "segments"]}  # akas filtered to these only
    idx = label.ImdbIndex(basics, votes, needed)
    n_akas = idx.add_akas(load.IMDB_DIR / "title.akas.tsv.gz", needed)
    print("akas hits loaded:", n_akas)

    rows = []
    for k in pick:
        r = ki.loc[k]
        rel = r["release_date"]
        rel_year = int(rel.year) if pd.notna(rel) else None
        tag_year = int(r["tag_year"]) if pd.notna(r["tag_year"]) else None
        m = idx.match(list(r["segments"]), r["type_known"], bool(r["series_tag_stripped"]), rel_year, tag_year)
        grp = label.genre_group(m["imdb_genres"], mapping) if m["matched"] else None
        rows.append({
            "key": ki.at[k, "key"], "kid": k, "netflix_title": r["rep_title"], "language_tag": "tagged" if r["tagged"] else "untagged",
            "netflix_type": r["type_known"], "release_year_used": rel_year, "tag_year": tag_year,
            "matched": m["matched"], "tconst": m["tconst"], "imdb_title": m["imdb_title"],
            "imdb_type": m["imdb_type"], "imdb_year": m["imdb_year"], "imdb_genres": m["imdb_genres"],
            "group": grp, "stage": m["stage"], "segments_matched": m["segments_matched"], "candidates_after_filter": m["candidates_after_filter"],
            "tie_break": m["tie_break"], "type_rule": m["type_rule"], "year_source": m["year_source"],
        })
    pilot = pd.DataFrame(rows)
    pilot["labelled"] = pilot["group"].notna()
    pilot.to_csv(OUT / "pilot_table.csv", index=False)
    rate = pilot["matched"].mean()
    print(f"PILOT match rate {rate:.3f} ({int(pilot['matched'].sum())}/30); labelled {pilot['labelled'].mean():.3f}")
    print(pilot.groupby("language_tag")[["matched", "labelled"]].mean().to_string())
    print(pilot.drop(columns=["tconst", "kid"]).to_string())
    if rate < PILOT_GATE:
        print(f"STOP: pilot match rate below {PILOT_GATE:.0%}.")
        sys.exit(5)
    print("Pilot done. Full-scope labelling is NOT run: waiting for workflow/05_pilot_check.md.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["manifest", "pilot", "full"])
    args = ap.parse_args()
    {"manifest": stage_manifest, "pilot": stage_pilot, "full": stage_full}[args.stage]()


if __name__ == "__main__":
    main()
