"""Consumer population: demographics and per-person frailty."""

import numpy as np

import config
from simulation import params


def build_population(rng):
    """Return dict of per-person arrays for the fixed population.

    Cell indexing: ai = age_idx * 3 + income_idx (0..11);
    cell48 = ai * 4 + region_idx (0..47).
    """
    n = config.N_POP
    p48 = (params.AGE_INCOME_P.reshape(12, 1) * params.REGION_P.reshape(1, 4)).ravel()
    p48 = p48 / p48.sum()
    counts = rng.multinomial(n, p48)
    cell48 = np.repeat(np.arange(48), counts)
    ai = cell48 // 4
    age_idx = (ai // 3).astype(np.int8)
    inc_idx = (ai % 3).astype(np.int8)
    reg_idx = (cell48 % 4).astype(np.int8)

    frailty = rng.lognormal(0.0, params.FRAILTY_SIGMA, n)
    frailty = frailty / np.exp(params.FRAILTY_SIGMA ** 2 / 2)  # mean 1

    return {
        "n": n,
        "age_idx": age_idx,
        "inc_idx": inc_idx,
        "reg_idx": reg_idx,
        "ai": ai.astype(np.int8),
        "cell48": cell48.astype(np.int8),
        "frailty": frailty,
    }


def census_tables(pop):
    """Actual population counts for the published census product: the
    age x income joint (12 cells) and the region margin (4 cells). The
    full 48-cell joint is deliberately not published."""
    ai_counts = np.bincount(pop["ai"], minlength=12)
    reg_counts = np.bincount(pop["reg_idx"], minlength=4)
    return ai_counts, reg_counts
