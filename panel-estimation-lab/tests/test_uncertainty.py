"""Bootstrap sanity: seeded (identical reruns) and centered (intervals
contain their own point estimates)."""

import numpy as np

from estimation import uncertainty


def test_bootstrap_is_seeded(engines):
    _, raw, cor = engines
    a, _ = uncertainty.bootstrap_cis(raw, cor, b_reps=4)
    b, _ = uncertainty.bootstrap_cis(raw, cor, b_reps=4)
    for m in a:
        for k in a[m]:
            assert (a[m][k][0] == b[m][k][0]).all()
            assert (a[m][k][1] == b[m][k][1]).all()


def test_intervals_contain_point_estimate(estimates):
    e = estimates[estimates["kpi"].isin(["revenue", "actives"])].copy()
    inside = ((e["ci_lo"] <= e["estimate"]) & (e["estimate"] <= e["ci_hi"]))
    assert inside.mean() > 0.98, f"{(~inside).sum()} interval rows exclude the point"
