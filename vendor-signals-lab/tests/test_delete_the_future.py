"""Delete-the-future: pivot t* = 2024Q4. Copy the tree, physically
delete every exhaust row dated after t* and every truth/outcome row
after t*, rerun coverage/composite/flags for quarters <= t*, and assert
those output slices are byte-identical to the as_of()-limited run over
the full, untruncated tree. This proves the temporal fence is enforced
by what the code reads, not merely by what it happens not to use.
"""

import shutil

import pandas as pd

import config
from estimation.loader import ShopData
from estimation import coverage, composite, inflection

PIVOT = "2024Q4"


def _truncate_tree(src_root, dst_root):
    shutil.copytree(src_root / "data", dst_root / "data")
    pivot_end = config.quarter_end_date(PIVOT)
    pivot_month_label = config.month_label(*config.quarter_months(PIVOT)[-1])

    jp = dst_root / "data" / "exhaust" / "job_postings.csv"
    df = pd.read_csv(jp, dtype=str)
    df[df["posted_date"] <= pivot_end].to_csv(jp, index=False, lineterminator="\n")

    wt = dst_root / "data" / "exhaust" / "web_traffic.csv"
    df = pd.read_csv(wt, dtype=str)
    df[df["month"] <= pivot_month_label].to_csv(wt, index=False, lineterminator="\n")

    sp = dst_root / "data" / "exhaust" / "spend_panel.csv"
    df = pd.read_csv(sp, dtype=str)
    df[df["txn_date"] <= pivot_end].to_csv(sp, index=False, lineterminator="\n")

    for name in ("inflections.csv", "outcome_events.csv", "disclosed_revenues.csv",
                 "truth_financials.csv"):
        p = dst_root / "data" / "truth" / name
        df = pd.read_csv(p, dtype=str)
        df = df[df["quarter"] <= PIVOT]
        df.to_csv(p, index=False, lineterminator="\n")


def _build_slice(root):
    shop = ShopData(root)
    cm, merged, _, _ = coverage.build(shop, PIVOT)
    withpct = composite.add_percentiles(merged)
    withcomp = composite.build_composite(withpct)
    flagged = inflection.add_flags(withcomp)
    return cm.reset_index(drop=True), flagged.reset_index(drop=True)


def test_delete_the_future_byte_identical(built, tmp_path):
    truncated_root = tmp_path / "truncated"
    truncated_root.mkdir()
    _truncate_tree(built["root"], truncated_root)

    cm_full, flagged_full = _build_slice(built["root"])
    cm_trunc, flagged_trunc = _build_slice(truncated_root)

    pd.testing.assert_frame_equal(
        cm_full.sort_values(["vendor_id", "quarter"]).reset_index(drop=True),
        cm_trunc.sort_values(["vendor_id", "quarter"]).reset_index(drop=True))

    cols = ["vendor_id", "quarter", "composite", "tier", "accel_flag", "stall_flag"]
    a = flagged_full[cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    b = flagged_trunc[cols].sort_values(["vendor_id", "quarter"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_as_of_boundary_inclusive_exact(built):
    shop = ShopData(built["root"])
    av_q2 = shop.as_of("2023Q2")
    q2_end = config.quarter_end_date("2023Q2")
    assert (av_q2.jobs["posted_date"] <= q2_end).all()

    q3_start_month = config.month_label(*config.quarter_months("2023Q3")[0])
    assert (av_q2.web["month"] < q3_start_month).all()

    # spend publication lag: a transaction dated in the last month of a
    # quarter is not visible as-of that same quarter's close.
    last_month = config.quarter_months("2023Q2")[-1]
    last_month_label = config.month_label(*last_month)
    full_spend = shop.spend_panel()
    in_last_month = full_spend[full_spend["txn_date"].str.slice(0, 7) == last_month_label]
    if not in_last_month.empty:
        visible_ids = set(zip(av_q2.spend["txn_date"], av_q2.spend["panelist_id"],
                               av_q2.spend["amount"]))
        for _, row in in_last_month.iterrows():
            key = (row["txn_date"], row["panelist_id"], row["amount"])
            assert key not in visible_ids, "last-month spend row leaked past its publication lag"
