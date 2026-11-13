"""Unit tests for the Q1 analysis functions on synthetic data (no real data needed)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import analyze as an  # noqa: E402


def _perfect_alternator(amp=3.0):
    """Two genres, seven halves: A is high in H2, low in H1; B is the complement."""
    a = np.array([40, 40 + amp, 40, 40 + amp, 40, 40 + amp, 40], dtype=float)
    return np.vstack([a, 100 - a])


def test_margin_perfect_alternator_up():
    S = _perfect_alternator(3.0)
    up, down = an.margins(an.shifts(S))
    assert np.isclose(up[0], 3.0) and np.isclose(down[1], 3.0)  # A peaks in H2, B is the mirror
    assert down[0] == -3.0


def test_genre_margin_and_direction():
    S = _perfect_alternator(3.0)
    v = an.Variants(S, S, S.copy(), S.copy())
    g, d = an.genre_margin(an.variant_margins(v))
    assert np.isclose(g[0], 3.0) and d[0] == 0 and d[1] == 1


def test_check3_uses_five_transitions_and_nan_never_passes():
    S = _perfect_alternator(3.0)
    nan = S.copy()
    nan[:, 0] = np.nan
    m = an.variant_margins(an.Variants(S, S, nan, nan))
    assert np.isclose(m["c3n"][0, 0], 3.0)  # d2..d6 with signs (-,+,-,+,-)
    bad = S.copy()
    bad[:, 3] = np.nan
    g, _ = an.genre_margin(an.variant_margins(an.Variants(S, S, bad, bad)))
    assert np.isneginf(g).all()


def test_group_shares_sum_to_100_and_mask():
    H = np.array([[10.0, 10.0], [30.0, 10.0], [60.0, 80.0]])
    G = np.eye(3)
    S = an.group_shares(H, G)
    assert np.allclose(S.sum(axis=0), 100)
    S2 = an.group_shares(H, G, mask=np.array([[0, 1], [1, 1], [1, 1]], dtype=bool))
    assert np.isclose(S2[0, 0], 0.0) and np.isclose(S2[1, 0], 100 * 30 / 90)


def test_permutation_identity_counted_and_count_of_perfect_orderings():
    S = _perfect_alternator(3.0)
    v = an.Variants(S, S, S.copy(), S.copy())
    out, Ms = an.permutation_test(v, np.array([0, 1]), thetas=(2.0,), fix_first=False)
    assert out["n_orderings"] == 5040
    # orderings where the 7 positions alternate low/high in the right way: 4 H1 slots (high-free) and
    # 3 H2 slots; with only 2 distinct values the pattern passes iff the high ones fill the 3 'up' slots
    # (B is the mirror of A, so B passes "down" in exactly the same orderings): 3! x 4! = 144 orderings
    assert out["any_pass_count"]["2.0"] == 6 * 24
    assert out["p_value"] == out["any_pass_fraction"]["2.0"]


def test_bootstrap_is_seeded_and_cluster_based():
    rng = np.random.default_rng(0)
    H = rng.uniform(1, 10, size=(60, 7))
    G = np.zeros((60, 2))
    G[np.arange(60), np.arange(60) % 2] = 1
    top = np.zeros((60, 7), dtype=bool)
    new = np.zeros((60, 7), dtype=bool)
    car = np.ones((60, 7), dtype=bool)
    new[:, 0] = car[:, 0] = False
    a = an.cluster_bootstrap(H, G, top, new, car, np.array([0, 1]), np.array([0, 0]), n_boot=20, seed=1)
    b = an.cluster_bootstrap(H, G, top, new, car, np.array([0, 1]), np.array([0, 0]), n_boot=20, seed=1)
    assert np.allclose(a["shift"], b["shift"])
    # two genres sum to 100 each half, so their shifts are exact mirrors in every replicate
    assert np.allclose(a["shift"][:, 0], -a["shift"][:, 1])


def test_pair_rule_links_mirror_genres():
    x = np.array([2, -2, 3, -1, 2.5, -2.0])
    comps, pairs = an.pair_rule(np.vstack([x, -x, np.array([1, 1, -1, 1, -1, 1.0])]), ["A", "B", "C"])
    assert sorted(map(sorted, comps)) == [["A", "B"], ["C"]]


def test_newcombe_matches_known_value():
    d, lo, hi = an.newcombe_diff(56, 70, 48, 80)  # Newcombe (1998) example: 0.8 - 0.6
    assert np.isclose(d, 0.2) and np.isclose(lo, 0.0524, atol=2e-3) and np.isclose(hi, 0.3339, atol=2e-3)


def test_build_matrices_new_vs_carried():
    hk = pd.DataFrame({
        "half": ["H1 2023", "H2 2023", "H2 2023", "H1 2024", "H1 2024"],
        "kid": ["a [film]", "a [film]", "b [series]", "b [series]", "c [film]"],
        "key": ["a", "a", "b", "b", "c"],
        "hours": [5.0, 6.0, 7.0, 8.0, 9.0],
    })
    halves = ["H1 2023", "H2 2023", "H1 2024"]
    H, top10, new, car = an.build_matrices(hk, halves, ["a [film]", "b [series]", "c [film]"])
    assert car[0, 1] and new[1, 1]  # a carried in H2 2023, b new
    assert not new[1, 2]            # b present in both H2 2023 and H1 2024
    assert car[1, 2] and new[2, 2] and not car[2, 2]
    assert top10.sum() == 5  # fewer than 10 keys per half: all are 'top 10'
