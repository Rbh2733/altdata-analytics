"""Ladder claims, matched to mechanism rather than asserted as blanket
monotonicity. Each assertion names why it should hold; the one place the
spec's expected pattern did not survive contact with the data (the
duplicate-day quarter, where feed inflation accidentally offsets the
panel's under-capture) is asserted for what actually happens and
narrated in the README."""

import numpy as np
import pandas as pd

import config


def _mape(cells, method, kpi, quarters=None):
    c = cells[(cells["method"] == method) & (cells["kpi"] == kpi)]
    if quarters is not None:
        c = c[c["quarter"].isin(quarters)]
    return c["ape"].mean()


def _cells(root):
    return pd.read_csv(root / "outputs" / "scorecard.csv")


def test_m2_beats_m1_on_market_share(root):
    cells = _cells(root)
    assert _mape(cells, "m2", "market_share") < _mape(cells, "m1", "market_share")


def test_m3_beats_m2_on_outage_and_descriptor_quarters(root, events):
    cells = _cells(root)
    for name in ("supplier_outage", "descriptor_change"):
        q = events[events["pathology"] == name]["quarter"].iloc[0]
        assert _mape(cells, "m3", "revenue", [q]) < _mape(cells, "m2", "revenue", [q]), name


def test_dedupe_moves_the_dup_quarter_back_to_baseline(root, events, estimates):
    """The duplicate day inflates m2 upward into its own under-capture
    bias, so m2's error that quarter is accidentally low; the honest
    claim for m3 is direction and baseline, not a smaller error."""
    cells = _cells(root)
    q = events[events["pathology"] == "duplicate_feed_day"]["quarter"].iloc[0]
    est = estimates[(estimates["kpi"] == "revenue") & (estimates["quarter"] == q)]
    for co in ("Vantry", "Glimmerly"):
        m2 = float(est[(est["method"] == "m2") & (est["company"] == co)]["estimate"].iloc[0])
        m3 = float(est[(est["method"] == "m3") & (est["company"] == co)]["estimate"].iloc[0])
        assert m3 < m2, f"dedupe failed to remove inflation for {co}"
    m3_q = _mape(cells, "m3", "revenue", [q])
    m3_all = cells[(cells["method"] == "m3") & (cells["kpi"] == "revenue")] \
        .groupby("quarter")["ape"].mean().median()
    assert abs(m3_q - m3_all) < 0.06, "corrected quarter not at m3's own baseline"


def test_m4_beats_m3_and_m1_aggregate_revenue(root):
    cells = _cells(root)
    assert _mape(cells, "m4", "revenue") < _mape(cells, "m3", "revenue")
    assert _mape(cells, "m4", "revenue") < _mape(cells, "m1", "revenue")


def test_m2_share_wins_while_revenue_level_stays_low(root, estimates):
    """m2's honest split: shares improve because capture roughly cancels
    in ratios, while revenue levels sit well below truth."""
    cells = _cells(root)
    rev = cells[(cells["method"] == "m2") & (cells["kpi"] == "revenue")]
    truth_vs_est = (rev["estimate"] < rev["truth"]).mean()
    assert truth_vs_est > 0.9, "m2 revenue is not persistently below truth"
    assert _mape(cells, "m2", "market_share") < 0.5 * _mape(cells, "m2", "revenue")


def test_scorecard_covers_all_scored_cells(root):
    cells = _cells(root)
    assert len(cells) == 4 * 6 * len(config.SCORED_QUARTERS) * len(config.KPIS)
    assert cells["ape"].notna().all()


def test_coverage_statistic_matches_recount_from_estimates_and_truth(
        root, estimates, truth, metrics):
    e = estimates[(estimates["scored"] == 1) & (estimates["kpi"] == "revenue")
                  & (estimates["method"] == "m4")]
    t = truth[["company", "quarter", "revenue"]]
    m = e.merge(t, on=["company", "quarter"])
    assert len(m) == 48
    covered = ((m["ci_lo"] <= m["revenue"]) & (m["revenue"] <= m["ci_hi"])).mean()
    assert abs(covered - metrics["coverage"]["m4"]["revenue"]) < 1e-6
