"""Web-source features: QA-corrected quarterly visits and within-vendor
log growth. The composite consumes only the growth column; levels are
never comparable across vendors (see estimation/levels.py's disclosed
exception for the one place a level is used at all).
"""

import numpy as np
import pandas as pd

import config
from estimation import qa


def compute(shop, as_of_quarter: str) -> pd.DataFrame:
    av = shop.as_of(as_of_quarter)
    covered = shop.web_covered_vendors().set_index("vendor_id")["covered"].to_dict()

    dm = shop.descriptor_map()
    bridge, _ = qa.detect_descriptor_fragmentation(av.spend, dm)
    resolved = qa.resolve_spend(av.spend, dm, bridge)
    spikes = qa.detect_bot_spikes(av.web, av.jobs, resolved)
    web = qa.winsorize_web(av.web, spikes)

    quarters = config.QUARTERS[:config.quarter_index(as_of_quarter) + 1]
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
