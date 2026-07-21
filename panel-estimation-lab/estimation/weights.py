"""Post-stratification by raking (iterative proportional fitting).

The census product publishes the age x income joint (12 cells) and the
region margin (4 cells), not the full 48-cell joint, so weighting rakes
to the two published margins. Degenerate cells collapse by a fixed,
data-independent map; weights are trimmed at 5x the weighted median with
one re-rake pass.
"""

import numpy as np

RAKE_TOL = 1e-8
RAKE_MAX_ITER = 200
MIN_CELL = 5
TRIM_CAP = 5.0

# Fixed collapse map on the age x income axis (ai = age * 3 + income):
# step 1 merges adjacent age bands within income (18-29 with 30-44,
# 45-59 with 60+); step 2 merges income low with mid.
_STEP1 = {0: 0, 3: 0, 1: 1, 4: 1, 2: 2, 5: 2,     # ages 0,1 by income
          6: 3, 9: 3, 7: 4, 10: 4, 8: 5, 11: 5}   # ages 2,3 by income
_STEP1_GROUPS = {0: [0, 3], 1: [1, 4], 2: [2, 5],
                 3: [6, 9], 4: [7, 10], 5: [8, 11]}
_STEP2_FROM1 = {0: 0, 1: 0, 2: 1, 3: 2, 4: 2, 5: 3}  # low+mid merged


def collapse_map(counts_ai: np.ndarray) -> np.ndarray:
    """Return group id per ai cell (12,). A step-1 group collapses when
    any of its member cells is under MIN_CELL; a collapsed group merges
    further (step 2) if it is still under MIN_CELL."""
    group = np.arange(12)
    step1_needed = {g: any(counts_ai[c] < MIN_CELL for c in cells)
                    for g, cells in _STEP1_GROUPS.items()}
    for c in range(12):
        g1 = _STEP1[c]
        if step1_needed[g1]:
            group[c] = 12 + g1
    for g1, needed in step1_needed.items():
        if not needed:
            continue
        merged_count = sum(counts_ai[c] for c in _STEP1_GROUPS[g1])
        if merged_count < MIN_CELL:
            for c in _STEP1_GROUPS[g1]:
                group[c] = 24 + _STEP2_FROM1[g1]
    # renumber densely
    uniq = {g: i for i, g in enumerate(sorted(set(group.tolist())))}
    return np.array([uniq[g] for g in group])


def _ipf(table, row_target, col_target):
    t = table.astype(float).copy()
    t[t == 0] = 0.0
    for it in range(1, RAKE_MAX_ITER + 1):
        prev = t.copy()
        rs = t.sum(axis=1)
        t *= np.where(rs > 0, row_target / np.where(rs > 0, rs, 1.0), 0.0)[:, None]
        cs = t.sum(axis=0)
        t *= np.where(cs > 0, col_target / np.where(cs > 0, cs, 1.0), 0.0)[None, :]
        denom = np.where(prev > 0, prev, 1.0)
        if np.max(np.abs(t - prev) / denom) < RAKE_TOL:
            return t, it
    return t, RAKE_MAX_ITER


def _weighted_median(values, w):
    order = np.argsort(values)
    v, w = values[order], w[order]
    cum = np.cumsum(w)
    return float(v[np.searchsorted(cum, 0.5 * cum[-1])])


def rake_weights(ai, reg, mult, ai_margin, reg_margin):
    """Per-panelist weights raked to the published margins.

    ai, reg: cell indices per panelist (only rows with mult > 0 count).
    mult: multiplicity per panelist (bootstrap resampling; ones for the
    point estimate). Panelists with mult == 0 get weight 0.
    Returns (weights, diagnostics). weights already include mult == 0
    zeroing but NOT the mult factor itself (weighted sums should use
    mult * weights).
    """
    active = mult > 0
    counts_ai = np.bincount(ai[active], weights=mult[active], minlength=12)
    group = collapse_map(counts_ai)
    n_g = int(group.max()) + 1
    g_of_p = group[ai]

    table = np.zeros((n_g, 4))
    np.add.at(table, (g_of_p[active], reg[active]), mult[active])
    row_target = np.zeros(n_g)
    np.add.at(row_target, group, ai_margin)
    col_target = reg_margin * (row_target.sum() / reg_margin.sum())

    fitted, iters = _ipf(table, row_target, col_target)
    with np.errstate(divide="ignore", invalid="ignore"):
        cell_w = np.where(table > 0, fitted / np.where(table > 0, table, 1.0), 0.0)
    w = np.where(active, cell_w[g_of_p, reg], 0.0)

    cap = TRIM_CAP * _weighted_median(w[active], mult[active])
    trimmed = int(((w > cap) & active).sum())
    if trimmed:
        w = np.minimum(w, cap)
        table2 = np.zeros((n_g, 4))
        np.add.at(table2, (g_of_p[active], reg[active]), (mult * w)[active])
        fitted2, it2 = _ipf(table2, row_target, col_target)
        with np.errstate(divide="ignore", invalid="ignore"):
            adj = np.where(table2 > 0, fitted2 / np.where(table2 > 0, table2, 1.0), 0.0)
        w = w * np.where(active, adj[g_of_p, reg], 0.0)
        iters += it2

    diag = {
        "iterations": iters,
        "collapsed_groups": n_g,
        "trimmed": trimmed,
        "trimmed_frac": round(trimmed / max(int(active.sum()), 1), 4),
        "weight_sum": float((mult * w).sum()),
        "active_panelists": int(active.sum()),
    }
    return w, diag
