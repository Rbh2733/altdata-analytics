"""Percentile normalization and the composite health index.

Design belief, stated before any result is seen: spend is the highest-
fidelity source where present (real dollars, not a proxy), jobs is next
(a structural leading indicator), web is noisiest (traffic estimates are
inherently the loosest proxy for revenue health). That belief sets the
frozen weights below; it is not fitted to anything.
"""

import numpy as np
import pandas as pd

SOURCE_WEIGHTS = {"jobs": 0.35, "web": 0.20, "spend": 0.45}
TIER_C_SHRINKAGE = 0.5  # composite pulled this fraction of the way to 50


def add_percentiles(merged: pd.DataFrame) -> pd.DataFrame:
    df = merged.copy()
    df["jobs_present"] = df["jobs_status"].isin(["tracked_active", "tracked_zero"])
    df["web_present"] = df["web_status"] == "present"
    df["spend_present"] = df["spend_presence"] == "present"

    for col, present_col, pct_col in [
        ("jobs_growth", "jobs_present", "jobs_pct"),
        ("web_growth", "web_present", "web_pct"),
        ("spend_growth", "spend_present", "spend_pct"),
    ]:
        df[pct_col] = np.nan
        mask = df[present_col] & df[col].notna()
        if mask.any():
            ranks = df.loc[mask].groupby(["segment", "quarter"])[col].rank(pct=True) * 100.0
            df.loc[mask, pct_col] = ranks
    return df


def _weighted_composite(row):
    total_w, wsum = 0.0, 0.0
    for src, col in (("jobs", "jobs_pct"), ("web", "web_pct"), ("spend", "spend_pct")):
        v = row[col]
        if pd.notna(v):
            w = SOURCE_WEIGHTS[src]
            total_w += w * v
            wsum += w
    if wsum == 0:
        return 50.0
    return total_w / wsum


def build_composite(merged_with_pct: pd.DataFrame) -> pd.DataFrame:
    df = merged_with_pct.copy()
    df["composite_raw"] = df.apply(_weighted_composite, axis=1)
    df["composite"] = np.where(
        df["tier"] == "C",
        50.0 + TIER_C_SHRINKAGE * (df["composite_raw"] - 50.0),
        df["composite_raw"])
    return df


# ---------------------------------------------------------------------------
# Naive (no-QA) comparison, used only for the honest-failure narrative
# ---------------------------------------------------------------------------

def build_naive_variant(shop, as_of_quarter: str) -> pd.DataFrame:
    """Recomputes growth/percentiles/composite from *uncorrected* exhaust:
    raw job postings (no dedupe), raw web visits (no winsorize), and
    descriptor-map-only spend (no fragmentation bridge, no cliff
    demotion). Used solely to produce outputs/naive_vs_qa.csv; the main
    pipeline never reads this."""
    import config
    from estimation import qa

    av = shop.as_of(as_of_quarter)
    vdir = shop.vendor_directory()
    seg_by_vendor = vdir.set_index("vendor_id")["segment"].to_dict()
    tracked = shop.jobs_tracked_vendors().set_index("vendor_id")["tracked"].to_dict()
    covered = shop.web_covered_vendors().set_index("vendor_id")["covered"].to_dict()
    dm = shop.descriptor_map()

    jobs = av.jobs.copy()
    if not jobs.empty:
        jobs["quarter"] = jobs["posted_date"].map(qa._quarter_of_date)
        jcounts = jobs.groupby(["vendor_id", "quarter"]).size()
    else:
        jcounts = pd.Series(dtype=int)

    web = av.web.copy()
    if not web.empty:
        web["quarter"] = web["month"].map(
            lambda m: config.quarter_of_date(int(m[:4]), int(m[5:7])))
        wsum = web.groupby(["vendor_id", "quarter"])["estimated_visits"].sum()
    else:
        wsum = pd.Series(dtype=float)

    spend_naive = qa.resolve_spend(av.spend, dm, {})  # no bridge: known descriptors only
    if not spend_naive.empty:
        spend_naive["quarter"] = spend_naive["txn_date"].map(qa._quarter_of_date)
        ssum = spend_naive.groupby(["vendor_id", "quarter"])["amount"].sum()
    else:
        ssum = pd.Series(dtype=float)

    quarters = config.QUARTERS[:config.quarter_index(as_of_quarter) + 1]
    rows = []
    for vid, seg in seg_by_vendor.items():
        for qi, t in enumerate(quarters):
            n_j = float(jcounts.get((vid, t), 0))
            n_j_prev2 = None
            jg = None
            if qi >= 3:
                cur2 = (jcounts.get((vid, t), 0) + jcounts.get((vid, quarters[qi - 1]), 0)) / 2.0
                prior2 = (jcounts.get((vid, quarters[qi - 2]), 0) + jcounts.get((vid, quarters[qi - 3]), 0)) / 2.0
                jg = float(np.log(cur2 + 1) - np.log(prior2 + 1))
            wg = None
            if qi >= 1:
                cur = wsum.get((vid, t), 0.0)
                prev = wsum.get((vid, quarters[qi - 1]), 0.0)
                if cur > 0 and prev > 0:
                    wg = float(np.log(cur) - np.log(prev))
            sg = None
            if qi >= 1:
                cur = ssum.get((vid, t), 0.0)
                prev = ssum.get((vid, quarters[qi - 1]), 0.0)
                if cur > 0 and prev > 0:
                    sg = float(np.log(cur) - np.log(prev))
            rows.append({"vendor_id": vid, "segment": seg, "quarter": t,
                         "jobs_growth": jg, "web_growth": wg, "spend_growth": sg,
                         "jobs_present": bool(tracked.get(vid, 0)),
                         "web_present": bool(covered.get(vid, 0)) and wsum.get((vid, t), 0.0) > 0,
                         "spend_present": ssum.get((vid, t), 0.0) > 0})
    df = pd.DataFrame(rows)
    for col, present_col, pct_col in [
        ("jobs_growth", "jobs_present", "jobs_pct"),
        ("web_growth", "web_present", "web_pct"),
        ("spend_growth", "spend_present", "spend_pct"),
    ]:
        df[pct_col] = np.nan
        mask = df[present_col] & df[col].notna()
        if mask.any():
            ranks = df.loc[mask].groupby(["segment", "quarter"])[col].rank(pct=True) * 100.0
            df.loc[mask, pct_col] = ranks
    df["composite_naive"] = df.apply(_weighted_composite, axis=1)
    return df
