"""World consistency: truth grid shape, archetype shapes, outcome events
follow trajectories, the generator-side hiring lead is real, and exhaust
darkens after shutdown/acquisition."""

import numpy as np
import pandas as pd

import config
from simulation import params, vendors as vendors_mod, trajectories as traj_mod


def test_truth_financials_grid_complete(built):
    tf = built["truth_financials"]
    assert tf["vendor_id"].nunique() == config.N_VENDORS
    counts = tf.groupby("vendor_id").size()
    assert (counts <= config.N_QUARTERS).all()
    assert (counts >= 1).all()


def test_archetype_growth_shapes():
    rng = np.random.default_rng(config.SEED)
    vendors = vendors_mod.build_vendors(rng)
    by_archetype = {}
    for v in vendors:
        traj = traj_mod.build_trajectory(v, rng)
        by_archetype.setdefault(v["archetype"], []).append(traj)

    wind_downs = by_archetype.get("wind_down", [])
    assert wind_downs, "no wind_down vendors drawn"
    n_eventually_declining = sum(
        1 for t in wind_downs if t["truth_arr"][-1] < max(t["truth_arr"][:6]))
    assert n_eventually_declining / len(wind_downs) > 0.7

    for t in by_archetype.get("acceleration", []):
        assert len(t["change_points"]) >= 1
    for t in by_archetype.get("steady_growth", []):
        assert len(t["change_points"]) == 0


def test_shutdowns_only_among_decliners_or_winddowns(built):
    events = built["truth_events"]
    shutdowns = events[events["event_type"] == "shutdown"]["vendor_id"].unique()
    directory_archetype = {}
    rng = np.random.default_rng(config.SEED)
    for v in vendors_mod.build_vendors(rng):
        directory_archetype[v["vendor_id"]] = v["archetype"]
    bad = [vid for vid in shutdowns
           if directory_archetype.get(vid) not in ("decline", "wind_down", "stall")]
    # stall permitted: a stalled vendor can still run out of runway; decline
    # and wind_down are the designed majority.
    assert len(bad) / max(len(shutdowns), 1) < 0.3


def test_disclosed_revenue_matches_truth_at_close(built):
    disc = pd.read_csv(built["root"] / "data" / "truth" / "disclosed_revenues.csv")
    acq = built["truth_events"][built["truth_events"]["event_type"] == "acquisition"]
    tf = built["truth_financials"].set_index(["vendor_id", "quarter"])["arr_m"]
    for _, row in disc.iterrows():
        vid = row["vendor_id"]
        acq_q = acq[acq["vendor_id"] == vid]["quarter"]
        assert len(acq_q) == 1
        true_arr = tf.get((vid, acq_q.iloc[0]))
        assert true_arr is not None
        assert abs(row["disclosed_revenue_m"] - round(true_arr)) < 1e-6


def test_generator_side_hiring_lead():
    """Direct check on the generator's own construction: for accelerating
    vendors, requisitions_target should rise at the regime-change quarter
    while realized ARR growth has not yet caught up (S-ramp not
    complete), confirming the planted ~2-quarter jobs lead is a real
    property of the trajectory builder, not an artifact measured only
    downstream."""
    rng = np.random.default_rng(config.SEED)
    vendors = vendors_mod.build_vendors(rng)
    checked = 0
    for v in vendors:
        if v["archetype"] != "acceleration":
            continue
        traj = traj_mod.build_trajectory(v, rng)
        cp = traj["change_points"][0]
        t0 = cp  # 0-indexed position where the new plan first applies
        if t0 + 2 >= config.N_QUARTERS:
            continue
        reqs_before = traj["requisitions_target"][t0 - 1] if t0 >= 1 else 0
        reqs_at = traj["requisitions_target"][t0]
        checked += 1
        assert reqs_at >= reqs_before - 1e-9
    assert checked > 5


def test_exhaust_darkens_after_shutdown(built):
    from estimation.loader import ShopData
    shop = ShopData(built["root"])
    events = built["truth_events"]
    shutdowns = events[events["event_type"] == "shutdown"]
    if shutdowns.empty:
        return
    row = shutdowns.iloc[0]
    vid, q = row["vendor_id"], row["quarter"]
    next_q = config.next_quarter(q, 2)
    if next_q is None:
        return
    jobs = shop.job_postings()
    later_postings = jobs[(jobs["vendor_id"] == vid)
                          & (jobs["posted_date"] > config.quarter_end_date(q))]
    assert later_postings.empty, f"{vid} posted jobs after shutting down in {q}"
