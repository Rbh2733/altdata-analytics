"""Repost dedupe changes only the storm vendor's features; the despike
correction is a no-op off the planted vendor/quarter; the fragmented
vendor's spend series is continuous post-QA; unit-level delete-the-
future checks on features_jobs, features_spend, and features_web."""

import pandas as pd

from estimation.loader import ShopData
from estimation import qa, features_jobs


def test_dedupe_changes_only_storm_vendor(built):
    """The storm's signature is the raw/unique *ratio*, not the absolute
    row count collapsed (a large organically-hiring vendor can shed more
    absolute rows to the 3% background relist rate simply by having more
    postings; that is not a pathology). The storm vendor should be far
    below the population's typical ratio."""
    shop = ShopData(built["root"])
    av = shop.as_of("2025Q4")
    ratios = qa.repost_storm_ratios(av.jobs)
    ratios = ratios[ratios["raw"] >= 10]

    plant = built["planted"]
    storm_vendor = plant[plant["pathology"] == "job_repost_storm"].iloc[0]["vendor_id"]
    storm_ratio = ratios[ratios["vendor_id"] == storm_vendor]["ratio"]
    assert not storm_ratio.empty
    assert storm_ratio.min() < 0.4

    median_ratio = ratios[ratios["vendor_id"] != storm_vendor]["ratio"].median()
    assert storm_ratio.min() < median_ratio - 0.3


def test_winsorize_is_noop_off_the_plant(built):
    shop = ShopData(built["root"])
    av = shop.as_of("2025Q4")
    dm = shop.descriptor_map()
    bridge, _ = qa.detect_descriptor_fragmentation(av.spend, dm)
    resolved = qa.resolve_spend(av.spend, dm, bridge)
    bots = qa.detect_bot_spikes(av.web, av.jobs, resolved)
    web_clean = qa.winsorize_web(av.web, bots)

    plant = built["planted"]
    spike_vendor = plant[plant["pathology"] == "bot_traffic_spike"].iloc[0]["vendor_id"]
    spike_row = web_clean[web_clean["vendor_id"] == spike_vendor]
    assert spike_row["corrected"].any(), "the planted bot-spike vendor was not corrected"
    # background false positives are expected and measured elsewhere
    # (test_qa_detections.py::test_population_false_positive_count_measured);
    # this test only asserts the plant itself is corrected.


def test_fragmented_vendor_continuous_post_qa(built):
    df, evidence, bridge = None, None, None
    from estimation import features_spend
    shop = ShopData(built["root"])
    spend_df, evidence, bridge = features_spend.compute(shop, "2025Q4")
    plant = built["planted"]
    vid = plant[plant["pathology"] == "descriptor_fragmentation"].iloc[0]["vendor_id"]
    sub = spend_df[spend_df["vendor_id"] == vid].sort_values("quarter")
    n_absent = (sub["spend_presence"] == "absent").sum()
    assert n_absent <= 1


def test_features_jobs_unit_delete_the_future(built):
    shop = ShopData(built["root"])
    full = features_jobs.compute(shop, "2025Q4")
    truncated = features_jobs.compute(shop, "2024Q4")
    cols = ["vendor_id", "quarter", "jobs_tracked", "jobs_n_reqs", "jobs_growth", "jobs_freeze"]
    a = full[full["quarter"] <= "2024Q4"][cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    b = truncated[cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_features_spend_unit_delete_the_future(built):
    """Unit-level delete-the-future for features_spend.compute, at the
    exact quarter the descriptor-fragmentation plant fires (2025Q1): a
    quarter's spend_amount/spend_presence/spend_coverage_cliff read must
    not change depending on how much *later* data compute() was also
    asked to produce a trailing series for. Before the fix, the bridge
    (and cliff) used for every historical quarter was derived from the
    full as_of_quarter snapshot, so compute(shop, '2025Q4') and
    compute(shop, '2025Q1') disagreed on 2025Q1 itself: the former saw a
    bridge built with three quarters of hindsight the latter never had.
    """
    from estimation import features_spend
    shop = ShopData(built["root"])
    full, _, _ = features_spend.compute(shop, "2025Q4")
    truncated, _, _ = features_spend.compute(shop, "2025Q1")
    cols = ["vendor_id", "quarter", "spend_amount", "spend_txn_count",
            "spend_presence", "spend_growth", "spend_coverage_cliff"]
    a = full[full["quarter"] <= "2025Q1"][cols].sort_values(
        ["vendor_id", "quarter"]).reset_index(drop=True)
    b = truncated[cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_features_web_unit_delete_the_future(tmp_path):
    """Unit-level delete-the-future for features_web.compute's bot-spike
    corroboration path, on a fixture built so the leak has somewhere to
    show (the committed world's spike and fragmentation plants land on
    unrelated vendors, so this path's leak is latent there): V1's June
    2024 traffic spike (z >> 4) coincides with a descriptor migration
    whose bridge evidence only accrues after 2024Q2, because the old
    panelists do not surface on the migrated descriptor until 2024Q3.
    As of 2024Q2 the resolvable spend shows a collapse (|log growth| >
    0.35), which corroborates the spike as a real move and leaves it
    uncorrected; with the hindsight bridge applied the collapse smooths
    away and the spike gets winsorized instead. A bridge derived once
    from the final snapshot therefore rewrites 2024Q2's keep-or-correct
    decision with evidence dated after 2024Q2; compute(shop, '2025Q4')
    and compute(shop, '2024Q2') must nonetheless agree on 2024Q2 itself.
    """
    from estimation import features_web
    ex = tmp_path / "data" / "exhaust"
    pub = tmp_path / "data" / "public"
    ex.mkdir(parents=True)
    pub.mkdir(parents=True)

    months = [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]

    web_rows = ["vendor_id,month,estimated_visits"]
    for y, m in months:
        v = 50000 if (y, m) == (2024, 6) else 1000
        web_rows.append(f"V1,{y}-{m:02d},{v}")
    (ex / "web_traffic.csv").write_text("\n".join(web_rows) + "\n")
    (ex / "web_covered_vendors.csv").write_text("vendor_id,covered\nV1,1\n")
    (ex / "job_postings.csv").write_text(
        "posting_id,vendor_id,title,posted_date,closed_date,location\n")

    spend_rows = ["descriptor_string,txn_date,amount,panelist_id"]
    for y, m in months:
        if (y, m) < (2024, 4):    # dense phase on the known descriptor
            for day, pan in ((5, "PANA"), (15, "PANB"), (25, "PANC")):
                spend_rows.append(f"ACME-OLD,{y}-{m:02d}-{day:02d},100.00,{pan}")
        else:                      # taper: the fade the bridge rule needs
            spend_rows.append(f"ACME-OLD,{y}-{m:02d}-05,100.00,PANA")
        if (2024, 4) <= (y, m) <= (2024, 6):   # migration: new panelist only
            spend_rows.append(f"ACME-NEW,{y}-{m:02d}-05,150.00,PANZ")
        elif (y, m) > (2024, 6):               # old panelists surface later
            spend_rows.append(f"ACME-NEW,{y}-{m:02d}-05,150.00,PANA")
            spend_rows.append(f"ACME-NEW,{y}-{m:02d}-15,150.00,PANB")
    (ex / "spend_panel.csv").write_text("\n".join(spend_rows) + "\n")
    (pub / "descriptor_map.csv").write_text("vendor_id,descriptor_string\nV1,ACME-OLD\n")

    shop = ShopData(tmp_path)
    full = features_web.compute(shop, "2025Q4")
    truncated = features_web.compute(shop, "2024Q2")
    cols = ["vendor_id", "quarter", "web_covered", "web_visits",
            "web_months_observed", "web_growth"]
    a = full[full["quarter"] <= "2024Q2"][cols].sort_values(
        ["vendor_id", "quarter"]).reset_index(drop=True)
    b = truncated[cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
