"""Unit tests for the shared helpers (small synthetic inputs, no data files needed)."""
import numpy as np

from pipeline import analyze as A


def test_holm_monotone_and_bounded():
    adj = A.holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])
    assert (adj <= 1).all()


def test_concentration_n50_n80_top5():
    R = np.array([[50, 30, 10, 5, 3, 2, 0, 0]])
    c = A.concentration(R)
    assert c["n50"][0] == 1 and c["n80"][0] == 2
    assert abs(c["top5"][0] - 0.98) < 1e-9
    assert abs(c["active"][0] - 0.75) < 1e-9


def test_ranked_ties_by_id():
    ids = np.array([5, 3, 9])
    rid, _ = A.ranked(np.array([10, 10, 4]), ids)
    assert list(rid) == [3, 5, 9]


def test_cover_list_reaches_fraction():
    ids = np.arange(4)
    assert A.cover_list(np.array([40, 30, 20, 10]), ids, 0.5) == [0, 1]


def test_boot_weights_rows_sum_to_n():
    W = A.boot_weights(7, 50, np.random.default_rng(1))
    assert (W.sum(1) == 7).all()


def test_one_sided_p_never_zero():
    assert A.one_sided_boot_p(np.ones(2000), "greater") > 0
