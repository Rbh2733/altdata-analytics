"""Raking behaves: margins reproduce, degenerate cells collapse by the
fixed map, and trimming keeps weights bounded."""

import numpy as np

from estimation import weights


def test_raked_margins_match_published_margins_within_tolerance(engines):
    _, _, cor = engines
    W, diags = cor.raked_weights(np.ones(cor.P))
    q = 6  # 2023Q3, a mid-history quarter
    w = W[:, q]
    ai_hat = np.bincount(cor.ai, weights=w, minlength=12)
    reg_hat = np.bincount(cor.reg, weights=w, minlength=4)
    assert np.allclose(ai_hat, cor.ai_margin, rtol=0.02)
    assert np.allclose(reg_hat, cor.reg_margin, rtol=0.01)
    assert abs(w.sum() - cor.n_pop) / cor.n_pop < 0.01


def test_degenerate_cell_collapse_triggers_on_constructed_tiny_cell():
    counts = np.array([200, 150, 3, 90, 80, 40, 60, 50, 30, 20, 15, 10])
    group = weights.collapse_map(counts)
    # ai cell 2 (18-29 high) is under 5: it merges with its fixed partner,
    # ai cell 5 (30-44 high), and nothing else moves
    assert group[2] == group[5]
    assert group[0] != group[3]
    assert len(set(group.tolist())) < 12


def test_no_collapse_when_all_cells_populated():
    counts = np.full(12, 50)
    group = weights.collapse_map(counts)
    assert len(set(group.tolist())) == 12


def test_weights_positive_and_bounded_post_trim(engines):
    _, _, cor = engines
    W, diags = cor.raked_weights(np.ones(cor.P))
    assert (W >= 0).all()
    for q in range(12):
        w = W[:, q]
        active = w > 0
        med = np.median(w[active])
        assert w.max() <= 6.5 * med, f"quarter {q}: trim cap not holding"
