"""Unit cases for the one-month gap tolerance in subscription spells."""

import numpy as np

from estimation.methods import gap_fill


def _fill(bits):
    arr = np.array([bits], dtype=bool)
    return gap_fill(arr)[0].astype(int).tolist()


def test_single_gap_is_bridged():
    assert _fill([1, 0, 1]) == [1, 1, 1]


def test_double_gap_ends_the_spell():
    assert _fill([1, 0, 0, 1]) == [1, 0, 0, 1]


def test_leading_and_trailing_edges_never_fill():
    assert _fill([0, 1, 1, 0]) == [0, 1, 1, 0]
    assert _fill([1, 0]) == [1, 0]
    assert _fill([0, 1]) == [0, 1]


def test_mixed_sequence():
    assert _fill([1, 1, 0, 1, 0, 0, 1, 0, 1]) == [1, 1, 1, 1, 0, 0, 1, 1, 1]
