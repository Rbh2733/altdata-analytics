"""Truth is internally consistent: stock-flow identities hold, derived
KPIs recompute, and reported actuals are truth under the stated rounding
and nothing else."""

import numpy as np
import pandas as pd

import config


def test_truth_identities_hold(truth):
    t = truth.sort_values(["company", "quarter"]).reset_index(drop=True)
    # stock-flow identity, exact by construction
    assert (t["actives"] == t["prior_actives"] + t["gross_adds"] - t["churned"]).all()
    # prior_actives chains to the previous quarter's actives
    for co, g in t.groupby("company"):
        g = g.sort_values("quarter")
        assert (g["prior_actives"].to_numpy()[1:] == g["actives"].to_numpy()[:-1]).all()
    # churn_rate and arpu recompute from their parts
    cr = t["churned"] / t["prior_actives"]
    assert np.allclose(t["churn_rate"], cr, atol=1e-5)
    assert np.allclose(t["arpu"], t["revenue"] / t["actives"], rtol=1e-3)
    # market shares sum to 100 per quarter
    sums = t.groupby("quarter")["market_share"].sum()
    assert np.allclose(sums, 100.0, atol=0.01)


def test_reported_matches_truth_within_stated_rounding(root, truth):
    rep = pd.read_csv(root / "data" / "public" / "reported_actuals.csv")
    m = rep.merge(truth, on=["company", "quarter"], suffixes=("_rep", ""))
    assert len(m) == 6 * len(config.QUARTERS)
    assert (np.abs(m["revenue_rep"] - m["revenue"]) <= 50_000 + 1e-6).all()
    assert (np.abs(m["actives_rep"] - m["actives"]) <= 500).all()
