"""Spend-source features: descriptor-resolved (fragmentation-merged,
cliff-demoted) quarterly spend growth, gated by the presence rule.

The fragmentation bridge and coverage-cliff flags are re-derived at each
quarter's own information horizon, shop.as_of(t) for that specific t, not
once from the as_of_quarter snapshot handed to compute(). qa.detect_
descriptor_fragmentation's "recent" activity read is whatever is last in
the slice it is given: handing it the full as_of_quarter slice for every
historical quarter would let evidence from later quarters bridge (or fail
to bridge) a descriptor as of an earlier quarter, and the same shape of
leak applies to detect_coverage_cliff. Recomputing both per quarter t from
shop.as_of(t) mirrors the property features_jobs.compute already has
(dedupe_jobs is backward-looking only, verified by tests/test_features.py's
delete-the-future check) and closes the equivalent gap here.
"""

import numpy as np
import pandas as pd

import config
from estimation import qa


def compute(shop, as_of_quarter: str) -> pd.DataFrame:
    dm = shop.descriptor_map()
    vdir = shop.vendor_directory()
    seg_by_vendor = vdir.set_index("vendor_id")["segment"].to_dict()
    quarters = config.QUARTERS[:config.quarter_index(as_of_quarter) + 1]

    # Per-quarter resolved spend: bridge_t and cliff_t are each computed
    # from shop.as_of(t), so a vendor-quarter's bridge/cliff status can
    # never depend on data dated after t.
    qsum_by_q, qcount_by_q, cliff_by_q = {}, {}, {}
    evidence, bridge = [], {}
    for t in quarters:
        av_t = shop.as_of(t)
        bridge_t, evidence_t = qa.detect_descriptor_fragmentation(av_t.spend, dm)
        resolved_t = qa.resolve_spend(av_t.spend, dm, bridge_t)
        cliff_flags_t = qa.detect_coverage_cliff(resolved_t, vdir)
        cliff_by_q[t] = (set(zip(cliff_flags_t["segment"], cliff_flags_t["quarter"]))
                          if not cliff_flags_t.empty else set())

        if not resolved_t.empty:
            resolved_t = resolved_t.copy()
            resolved_t["quarter"] = resolved_t["txn_date"].map(qa._quarter_of_date)
            qsum_by_q[t] = resolved_t.groupby(["vendor_id", "quarter"])["amount"].sum()
            qcount_by_q[t] = resolved_t.groupby(["vendor_id", "quarter"]).size()
        else:
            qsum_by_q[t] = pd.Series(dtype=float)
            qcount_by_q[t] = pd.Series(dtype=int)

        if t == as_of_quarter:
            evidence, bridge = evidence_t, bridge_t

    rows = []
    for vid, seg in sorted(seg_by_vendor.items()):
        for qi, t in enumerate(quarters):
            qsum, qcount = qsum_by_q[t], qcount_by_q[t]
            amt = float(qsum.get((vid, t), 0.0))
            n_this = int(qcount.get((vid, t), 0))
            window = [quarters[qi - 1], t] if qi >= 1 else [t]
            n_trailing = sum(int(qcount.get((vid, w), 0)) for w in window)
            if n_trailing >= qa.SPEND_PRESENCE_MIN_TXN_TRAILING_2Q:
                presence = "present"
            elif n_trailing > 0:
                presence = "thin"
            else:
                presence = "absent"
            cliff_hit = (seg, t) in cliff_by_q[t]

            growth = None
            if qi >= 1 and presence == "present":
                prev_t = quarters[qi - 1]
                prev_amt = float(qsum.get((vid, prev_t), 0.0))
                if amt > 0 and prev_amt > 0:
                    growth = float(np.log(amt) - np.log(prev_amt))
            rows.append({
                "vendor_id": vid, "quarter": t, "spend_amount": amt,
                "spend_txn_count": n_this, "spend_presence": presence,
                "spend_growth": growth, "spend_coverage_cliff": cliff_hit,
            })
    return pd.DataFrame(rows), evidence, bridge
