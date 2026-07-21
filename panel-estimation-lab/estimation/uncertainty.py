"""Panelist-level nonparametric bootstrap.

The panelist is the sampling unit; resampling rows or days would fake
independence that transactions within a panelist do not have. Inside
each replicate the full estimator reruns: weights are re-raked, QA
corrections reapply (they are panelist-level aggregates), and the
calibration factors are recomputed from the replicate's own prior-
quarter estimates, so factor uncertainty propagates into rung 4.

Scope: revenue and actives, all four methods, all quarters. The rung-1
and rung-2 coverage failure is the point: a bootstrap measures variance,
not bias, and a confidently wrong interval is the textbook failure of
resampling under selection.
"""

import numpy as np

import config


def bootstrap_cis(raw_engine, cor_engine, b_reps=None, seed_offset=1):
    B = config.BOOTSTRAP_B if b_reps is None else b_reps
    rng = np.random.default_rng(np.random.SeedSequence([config.SEED, seed_offset]))
    P = raw_engine.P
    C = raw_engine.C
    kpis = ("revenue", "actives")
    draws = {m: {k: np.empty((B, C, 12)) for k in kpis}
             for m in ("m1", "m2", "m3", "m4")}
    for b in range(B):
        mult = np.bincount(rng.integers(0, P, P), minlength=P).astype(float)
        ests = {
            "m1": raw_engine.m1(mult),
            "m2": raw_engine.m2(mult),
        }
        m3 = cor_engine.m3(mult)
        ests["m3"] = m3
        ests["m4"] = cor_engine.m4(mult, m3_est=m3)
        for m, e in ests.items():
            for k in kpis:
                draws[m][k][b] = e[k]
    tail_p = (1.0 - config.CI_LEVEL) / 2.0
    cis = {}
    for m in draws:
        cis[m] = {}
        for k in kpis:
            lo = np.quantile(draws[m][k], tail_p, axis=0)
            hi = np.quantile(draws[m][k], 1.0 - tail_p, axis=0)
            cis[m][k] = (lo, hi)
    return cis, B
