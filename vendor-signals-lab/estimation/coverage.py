"""Per-vendor-quarter presence, tier (A/B/C), and tier_reason. Tier is
purely mechanical: A = all three sources present, B = exactly two,
C = one or zero. tracked_zero counts as jobs present for tiering (it is
an informative observed zero, not a missing read); a spend read below
the presence floor ("thin") counts as spend absent.

tier_reason token, first applicable in this order: full, no_spend_channel,
below_traffic_floor, untracked_jobs, coverage_cliff, post_shutdown_dark.
Design intent: "full" is checked first but is harmless to check first,
since by definition it cannot be true while any of the other conditions
also hold (they all require some source to be missing). Ordering
no_spend_channel before coverage_cliff is deliberate: a vendor that never
had a spend channel keeps that as its reason even during a cliff quarter,
since the cliff cannot claim credit for an absence that would have
happened regardless. post_shutdown_dark is inferred behaviorally (all
three sources newly silent after having had at least one present the
prior quarter) rather than from any truth label, since this layer cannot
read data/truth/.
"""

import pandas as pd

import config
from estimation import features_jobs, features_web, features_spend


def build(shop, as_of_quarter: str):
    jobs = features_jobs.compute(shop, as_of_quarter)
    web = features_web.compute(shop, as_of_quarter)
    spend, frag_evidence, bridge = features_spend.compute(shop, as_of_quarter)
    vdir = shop.vendor_directory().set_index("vendor_id")["segment"].to_dict()

    merged = jobs.merge(web, on=["vendor_id", "quarter"], how="outer") \
                 .merge(spend, on=["vendor_id", "quarter"], how="outer")
    merged["segment"] = merged["vendor_id"].map(vdir)

    def jobs_status(row):
        if not row["jobs_tracked"]:
            return "untracked"
        return "tracked_active" if row["jobs_n_reqs"] > 0 else "tracked_zero"

    def web_status(row):
        return "present" if row["web_months_observed"] > 0 else "absent"

    merged["jobs_status"] = merged.apply(jobs_status, axis=1)
    merged["web_status"] = merged.apply(web_status, axis=1)
    merged = merged.sort_values(["vendor_id", "quarter"]).reset_index(drop=True)

    # post_shutdown_dark: all three absent this quarter, and at least one
    # source was present for this vendor the prior quarter.
    merged["any_present"] = ((merged["jobs_status"] == "tracked_active")
                              | (merged["web_status"] == "present")
                              | (merged["spend_presence"] == "present"))
    merged["prior_any_present"] = merged.groupby("vendor_id")["any_present"].shift(1).fillna(False)
    merged["dark_now"] = ((merged["jobs_status"].isin(["untracked", "tracked_zero"]))
                           & (merged["web_status"] == "absent")
                           & (merged["spend_presence"] != "present"))
    merged["post_shutdown_dark"] = merged["dark_now"] & merged["prior_any_present"]

    def tier_reason(row):
        jobs_present = row["jobs_status"] in ("tracked_active", "tracked_zero")
        web_present = row["web_status"] == "present"
        spend_present = row["spend_presence"] == "present"
        if jobs_present and web_present and spend_present:
            return "full"
        if not spend_present and not row["spend_coverage_cliff"]:
            return "no_spend_channel"
        if not web_present:
            return "below_traffic_floor"
        if row["jobs_status"] == "untracked":
            return "untracked_jobs"
        if row["spend_coverage_cliff"]:
            return "coverage_cliff"
        if row["post_shutdown_dark"]:
            return "post_shutdown_dark"
        return "no_spend_channel"

    merged["tier_reason"] = merged.apply(tier_reason, axis=1)
    # post_shutdown_dark overrides everything once truly dark on all fronts
    merged.loc[merged["post_shutdown_dark"], "tier_reason"] = "post_shutdown_dark"

    def tier(row):
        jobs_present = row["jobs_status"] in ("tracked_active", "tracked_zero")
        web_present = row["web_status"] == "present"
        spend_present = row["spend_presence"] == "present"
        n = int(jobs_present) + int(web_present) + int(spend_present)
        return {3: "A", 2: "B"}.get(n, "C")

    merged["tier"] = merged.apply(tier, axis=1)

    out_cols = ["vendor_id", "segment", "quarter", "jobs_status", "jobs_n_reqs",
                "web_status", "web_months_observed", "spend_presence",
                "spend_txn_count", "tier", "tier_reason"]
    coverage_matrix = merged[out_cols].rename(columns={
        "jobs_n_reqs": "jobs_new_postings", "spend_presence": "spend_status"})
    return coverage_matrix, merged, frag_evidence, bridge
