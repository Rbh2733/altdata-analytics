"""Coverage tiers: tier recomputed from presence columns matches the
committed tier; spend coverage differs by segment; jobs coverage rises
with headcount; cliff quarters carry the coverage_cliff reason, not
no_spend_channel; the presence rule and jobs zero-vs-missing behave."""

import pandas as pd

from estimation import qa


def test_tier_recomputes_from_presence_columns(built):
    cm = built["coverage"]
    def expected_tier(row):
        jp = row["jobs_status"] in ("tracked_active", "tracked_zero")
        wp = row["web_status"] == "present"
        sp = row["spend_status"] == "present"
        n = int(jp) + int(wp) + int(sp)
        return {3: "A", 2: "B"}.get(n, "C")
    recomputed = cm.apply(expected_tier, axis=1)
    assert (recomputed == cm["tier"]).all()


def test_spend_coverage_differs_by_segment(built):
    cm = built["coverage"]
    present_rate = cm.groupby("segment").apply(
        lambda g: (g["spend_status"] == "present").mean())
    assert present_rate.max() - present_rate.min() > 0.10


def test_jobs_coverage_rises_with_headcount(built):
    directory = pd.read_csv(built["root"] / "data" / "public" / "vendor_directory.csv")
    tracked = pd.read_csv(built["root"] / "data" / "exhaust" / "jobs_tracked_vendors.csv")
    tf = built["truth_financials"]
    hc = tf[tf["quarter"] == "2023Q1"][["vendor_id", "headcount"]]
    merged = tracked.merge(hc, on="vendor_id")
    merged["decile"] = pd.qcut(merged["headcount"], 5, duplicates="drop")
    rates = merged.groupby("decile", observed=True)["tracked"].mean()
    rates = list(rates)
    assert rates[-1] > rates[0]
    # allow one local dip but require an overall rising trend
    increases = sum(1 for a, b in zip(rates, rates[1:]) if b >= a)
    assert increases >= len(rates) - 2


def test_cliff_quarters_carry_coverage_cliff_reason(built):
    cm = built["coverage"]
    plant = built["planted"]
    cliff_row = plant[plant["pathology"] == "coverage_cliff"].iloc[0]
    quarters = cliff_row["quarter"].split("|")
    seg = cliff_row["detail"].split("=")[1]
    sub = cm[(cm["segment"] == seg) & (cm["quarter"].isin(quarters))]
    # the cliff itself produces zero *new* spend rows that quarter; the
    # committed spend_status can still read 'present' briefly on the
    # trailing 2-quarter presence window carrying over pre-cliff data,
    # which is why tier_reason (not raw status) is the cliff's signature.
    assert (sub["spend_txn_count"] == 0).all()
    reason_counts = sub["tier_reason"].value_counts()
    assert reason_counts.get("coverage_cliff", 0) > 0


def test_spend_presence_thresholds():
    df = pd.DataFrame({
        "descriptor_string": ["D1"] * 10, "vendor_id": ["V1"] * 10,
        "txn_date": [f"2023-0{i%9+1}-01" for i in range(10)],
        "amount": [10.0] * 10, "panelist_id": ["P1"] * 10,
    })
    assert qa.spend_presence(df, "V1", "2023Q3") in ("present", "thin")
    empty = df.iloc[0:0]
    assert qa.spend_presence(empty, "V1", "2023Q3") == "absent"


def test_jobs_zero_vs_missing_distinct(built):
    cm = built["coverage"]
    assert (cm["jobs_status"] == "tracked_zero").any()
    assert (cm["jobs_status"] == "untracked").any()
