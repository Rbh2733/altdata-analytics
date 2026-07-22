"""Web-source features: QA-corrected quarterly visits and within-vendor
log growth. The composite consumes only the growth column; levels are
never comparable across vendors (see estimation/levels.py's disclosed
exception for the one place a level is used at all).

The bot-spike corroboration read is re-derived at each quarter's own
information horizon, shop.as_of(t) for that specific t, not once from
the as_of_quarter snapshot handed to compute(). qa.detect_bot_spikes's
no-corroboration filter resolves spend through the descriptor-
fragmentation bridge, and qa.detect_descriptor_fragmentation's "recent"
activity read is whatever is last in the slice it is given: handing it
the full as_of_quarter slice for every historical quarter would let
bridge evidence (and lag-delayed spend) dated after quarter t decide
whether quarter t's z>4 candidate gets corrected. Recomputing the
bridge, the resolved spend, and the corroboration per quarter t from
shop.as_of(t) mirrors the fix already applied to features_spend.compute
(see that module's docstring) and closes the same shape of leak on the
web side. The spike *candidates* were never at risk: bot_spike_flags is
backward-looking by construction (trailing-window returns only), as is
the winsorize correction itself (trailing median).
"""

import numpy as np
import pandas as pd

import config
from estimation import qa


def compute(shop, as_of_quarter: str) -> pd.DataFrame:
    av = shop.as_of(as_of_quarter)
    covered = shop.web_covered_vendors().set_index("vendor_id")["covered"].to_dict()
    dm = shop.descriptor_map()
    quarters = config.QUARTERS[:config.quarter_index(as_of_quarter) + 1]

    # Per-quarter spike corroboration: bridge_t, resolved_t, and the
    # jobs/web slices are each taken from shop.as_of(t), so quarter t's
    # keep-or-correct decision can never depend on data dated after t.
    spike_parts = []
    for t in quarters:
        av_t = shop.as_of(t)
        bridge_t, _ = qa.detect_descriptor_fragmentation(av_t.spend, dm)
        resolved_t = qa.resolve_spend(av_t.spend, dm, bridge_t)
        spikes_t = qa.detect_bot_spikes(av_t.web, av_t.jobs, resolved_t)
        if not spikes_t.empty:
            spike_parts.append(spikes_t[spikes_t["quarter"] == t])
    spikes = (pd.concat(spike_parts, ignore_index=True) if spike_parts
              else pd.DataFrame())
    web = qa.winsorize_web(av.web, spikes)
    if not web.empty:
        web = web.copy()
        web["quarter"] = web["month"].map(
            lambda m: config.quarter_of_date(int(m[:4]), int(m[5:7])))
        qsum = web.groupby(["vendor_id", "quarter"])["estimated_visits"].sum()
        qmonths = web.groupby(["vendor_id", "quarter"]).size()
        logv = {(r.vendor_id, r.month): np.log(max(r.estimated_visits, 1.0))
                for r in web.itertuples()}
    else:
        qsum, qmonths, logv = pd.Series(dtype=float), pd.Series(dtype=int), {}

    rows = []
    for vid in sorted(covered.keys()):
        cov = int(covered[vid])
        for qi, t in enumerate(quarters):
            visits = float(qsum.get((vid, t), 0.0))
            months_obs = int(qmonths.get((vid, t), 0))
            growth = None
            if qi >= 1:
                cur_months = config.quarter_months(t)
                prior_months = config.quarter_months(quarters[qi - 1])
                cur_vals = [logv[(vid, config.month_label(*m))]
                            for m in cur_months if (vid, config.month_label(*m)) in logv]
                prior_vals = [logv[(vid, config.month_label(*m))]
                              for m in prior_months if (vid, config.month_label(*m)) in logv]
                if cur_vals and prior_vals:
                    growth = float(np.mean(cur_vals) - np.mean(prior_vals))
            rows.append({
                "vendor_id": vid, "quarter": t, "web_covered": cov,
                "web_visits": visits, "web_months_observed": months_obs,
                "web_growth": growth,
            })
    return pd.DataFrame(rows)
