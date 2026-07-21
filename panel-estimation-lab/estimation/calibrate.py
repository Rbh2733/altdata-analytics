"""Ratio calibration to previously reported quarters.

For company c, target quarter q, KPI k in {revenue, actives}:
factor(c, q, k) = geometric mean, over the up-to-3 most recent quarters
j < q with reported actuals available, of reported(c, j, k) divided by
the rung-3 estimate(c, j, k). Minimum one prior quarter; when none
exists the factor falls back to 1.0 (with four warmup quarters that
fallback never fires for a scored quarter, but the rule exists in code).

Reported data reaches the estimation layer only through
loader.reported_before, which enforces the temporal fence; this module
just does arithmetic on what that gate returns.

Stated assumptions (also in the README): (a) the panel-to-population
capture ratio is locally stable across adjacent quarters; (b) post-
weighting composition is stable, so the ratio is not proxying a
composition trend; (c) reported KPI definitions match panel-derived
definitions; (d) no structural break sits between the calibration
window and the target quarter. Assumption (d) is deliberately violated
once in this world, and the scorecard shows what that costs.
"""

import numpy as np

CALIBRATION_WINDOW = 3


def factor_grid(reported, estimates):
    """Vectorized-enough factor computation.

    reported: [C, 12] with NaN where no reported value is available.
    estimates: [C, 12] rung-3 estimates for the same KPI (same
    multiplicity vector, so bootstrap replicates calibrate against
    their own history and factor uncertainty propagates).
    Returns factors [C, 12]; column q uses columns j < q only.
    """
    C, NQ = reported.shape
    f = np.ones((C, NQ))
    for c in range(C):
        for q in range(NQ):
            ratios = []
            for j in range(q - 1, -1, -1):
                if np.isnan(reported[c, j]) or estimates[c, j] <= 0:
                    continue
                ratios.append(reported[c, j] / estimates[c, j])
                if len(ratios) == CALIBRATION_WINDOW:
                    break
            if ratios:
                f[c, q] = float(np.exp(np.mean(np.log(ratios))))
    return f
