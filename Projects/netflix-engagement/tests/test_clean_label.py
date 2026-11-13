"""Unit tests for title cleaning, scope and genre grouping on synthetic data."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import clean, label  # noqa: E402


def test_season_tag_and_language_tag():
    c = clean.clean_title("Squid Game: Season 2 // 오징어 게임: 시즌 2", "series")
    assert c.key == "squid game" and c.tagged and c.series_tag_stripped
    assert c.segments[1] == "오징어 게임"


def test_subtitle_after_season_is_dropped_but_spinoff_name_kept():
    assert clean.clean_title("Squid Game: The Challenge: Season 1", "series").key == "squid game: the challenge"
    assert clean.clean_title("Show: Season 1: Pilot Special", "series").key == "show"


def test_year_tag_becomes_hint():
    c = clean.clean_title("Suits (2011): Season 1", "series")
    assert c.key == "suits" and c.tag_year == 2011


def test_film_titles_keep_numbers_and_volumes():
    assert clean.clean_title("Kill Bill: Vol. 1", "film").key == "kill bill: vol. 1"
    assert clean.clean_title("Fast & Furious 9", "film").key == "fast & furious 9"


def test_trailing_number_only_for_series():
    assert clean.clean_title("Stranger Things 4", "series").key == "stranger things"
    c = clean.clean_title("Stranger Things 4", "unknown")
    assert c.key == "stranger things 4" and c.base_without_trailing_number == "stranger things"


def test_limited_and_part():
    assert clean.clean_title("Adolescence: Limited Series", "series").key == "adolescence"
    assert clean.clean_title("Money Heist: Part 5", "series").key == "money heist"


def test_unknown_rows_resolved_against_series_keys_and_merge():
    raw = pd.DataFrame({
        "half": ["H1 2023", "H1 2023", "H2 2023", "H2 2023"],
        "title": ["Stranger Things 4", "Fast & Furious 9", "Stranger Things", "Stranger Things 4"],
        "hours_viewed": [10.0, 5.0, 7.0, 3.0],
        "release_date": [pd.NaT] * 4,
        "content_type": ["unknown", "unknown", "series", "series"],
        "is_other": [False] * 4, "sheet": ["x"] * 4,
    })
    out = clean.clean_reports(raw)
    hk = out.half_keys.set_index(["half", "kid"])["hours"]
    # H1 2023 type is taken from H2 2023 (one type there); an unseen title stays unknown
    assert hk[("H1 2023", "stranger things [series]")] == 10.0
    assert hk[("H1 2023", "fast & furious 9 [unknown]")] == 5.0
    assert hk[("H2 2023", "stranger things [series]")] == 10.0  # seasons merged by sum


def test_scope_counts_target():
    hk = pd.DataFrame({"half": ["a"] * 4, "key": list("wxyz"), "hours": [50.0, 30.0, 15.0, 5.0]})
    sc = clean.scope_counts(hk, targets=(0.80, 0.90))
    assert list(sc["n_a"]) == [2, 3] and list(sc["union_keys"]) == [2, 3]


def test_norm_title_and_genre_group():
    assert label.norm_title("Grey’s Anatomy") == label.norm_title("Greys  Anatomy!")
    assert label.norm_title("Pokémon") == "pokemon"
    m = pd.DataFrame({"imdb_genre": ["Drama", "Crime", "Short"], "group": ["Drama", "Crime & Thriller", ""],
                      "group_priority": [8.0, 5.0, float("nan")]})
    assert label.genre_group("Drama,Crime", m) == "Crime & Thriller"
    assert label.genre_group("Short", m) is None
    assert label.genre_group(None, m) is None
    assert label.check_genres_covered({"Drama", "Odd"}, m) == ["Odd"]


def test_match_filters_and_tiebreak():
    basics = pd.DataFrame({
        "tconst": ["tt1", "tt2", "tt3"], "titleType": ["movie", "movie", "tvSeries"],
        "primaryTitle": ["Alpha", "Alpha", "Alpha"], "originalTitle": ["Alpha"] * 3,
        "startYear": [2019.0, 2010.0, 2020.0], "genres": ["Drama", "Comedy", "Crime"],
    })
    idx = label.ImdbIndex(basics, {"tt1": 5, "tt2": 100, "tt3": 1}, {"alpha"})
    m = idx.match(["alpha"], "film", False, 2020, None)  # year filter removes tt2 (2010)
    assert m["tconst"] == "tt1" and m["year_source"] == "release_date"
    m = idx.match(["alpha"], "film", False, None, None)  # no year: most votes wins
    assert m["tconst"] == "tt2" and m["tie_break"] == "votes"
    m = idx.match(["alpha"], "series", False, None, None)
    assert m["tconst"] == "tt3"


def test_type_in_key_splits_collisions():
    raw = pd.DataFrame({
        "half": ["H2 2023", "H2 2023"], "title": ["Dark", "Dark"], "hours_viewed": [4.0, 6.0],
        "release_date": [pd.NaT] * 2, "content_type": ["film", "series"], "is_other": [False] * 2, "sheet": ["x"] * 2,
    })
    out = clean.clean_reports(raw)
    assert set(out.half_keys["kid"]) == {"dark [film]", "dark [series]"}
    assert out.log["collisions_before_type_in_key"]["within_half_collision_pairs"] == 1


def test_tagged_title_prefers_candidate_found_by_two_segments():
    basics = pd.DataFrame({
        "tconst": ["tt1", "tt2"], "titleType": ["movie", "movie"],
        "primaryTitle": ["Alpha", "Beta"], "originalTitle": ["Beta", "Beta"],
        "startYear": [2020.0, 2020.0], "genres": ["Drama", "Comedy"],
    })
    # tt1 is found by segment 1 (primary) and segment 2 (original); tt2 by segment 2 only, with more votes
    idx = label.ImdbIndex(basics, {"tt1": 1, "tt2": 99}, {"alpha", "beta"})
    m = idx.match(["alpha", "beta"], "film", False, None, None)
    assert m["tconst"] == "tt1" and m["tie_break"] == "multi_segment" and m["segments_matched"] == "1,2"


def test_akas_only_used_when_stage1_has_no_candidate():
    basics = pd.DataFrame({"tconst": ["tt1", "tt2"], "titleType": ["movie", "movie"],
                           "primaryTitle": ["Alpha", "Zeta"], "originalTitle": ["Alpha", "Zeta"],
                           "startYear": [2020.0, 2020.0], "genres": ["Drama", "Comedy"]})
    idx = label.ImdbIndex(basics, {}, {"alpha", "gamma"})
    idx.akas_by_norm["alpha"] = [1]
    idx.akas_by_norm["gamma"] = [1]
    assert idx.match(["alpha"], "film", False, None, None)["stage"] == "stage1"
    assert idx.match(["gamma"], "film", False, None, None)["stage"] == "stage2_akas"
