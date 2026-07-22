"""Jobs-source features: post-QA unique active requisitions, growth,
hiring-freeze indicator, and a supplementary tagger function-mix cut.

Every function here takes `as_of_quarter`, the latest quarter to
include, and routes all reads through loader.as_of(). Deduping is done
once over that as-of slice; because the relist-collapse window only
looks backward, a requisition's first-seen quarter is stable regardless
of how much later exhaust exists, so this is safe under the delete-the-
future test without any special-casing.
"""

import numpy as np
import pandas as pd

import config
from estimation import qa, tagger_mock


def compute(shop, as_of_quarter: str) -> pd.DataFrame:
    av = shop.as_of(as_of_quarter)
    tracked = shop.jobs_tracked_vendors().set_index("vendor_id")["tracked"].to_dict()

    deduped = qa.dedupe_jobs(av.jobs)
    if not deduped.empty:
        deduped = deduped.copy()
        deduped["quarter"] = deduped["posted_date"].map(qa._quarter_of_date)
        deduped["function"] = tagger_mock.tag_titles(deduped["title"])
        counts = deduped.groupby(["vendor_id", "quarter"]).size()
        func_counts = (deduped.groupby(["vendor_id", "quarter", "function"])
                       .size().unstack(fill_value=0))
        for f in tagger_mock.FUNCTIONS:
            if f not in func_counts.columns:
                func_counts[f] = 0
        func_shares = func_counts.div(func_counts.sum(axis=1), axis=0)
    else:
        counts = pd.Series(dtype=int)
        func_shares = pd.DataFrame()

    quarters = config.QUARTERS[:config.quarter_index(as_of_quarter) + 1]
    rows = []
    for vid in sorted(tracked.keys()):
        trk = int(tracked[vid])
        n_hist = [int(counts.get((vid, t), 0)) for t in quarters]
        for qi, t in enumerate(quarters):
            n = n_hist[qi]
            growth = None
            if qi >= 3:
                cur2 = (n_hist[qi] + n_hist[qi - 1]) / 2.0
                prior2 = (n_hist[qi - 2] + n_hist[qi - 3]) / 2.0
                growth = float(np.log(cur2 + 1) - np.log(prior2 + 1))
            freeze = False
            if trk and qi >= 1:
                had_activity = any(x > 0 for x in n_hist[:qi])
                if had_activity and n_hist[qi] == 0 and n_hist[qi - 1] == 0:
                    freeze = True
            func_mix = {f: 0.0 for f in tagger_mock.FUNCTIONS}
            if not func_shares.empty and (vid, t) in func_shares.index:
                r = func_shares.loc[(vid, t)]
                for k in func_mix:
                    func_mix[k] = float(r.get(k, 0.0))
            row = {
                "vendor_id": vid, "quarter": t, "jobs_tracked": trk,
                "jobs_n_reqs": n, "jobs_growth": growth, "jobs_freeze": freeze,
            }
            for f in tagger_mock.FUNCTIONS:
                row[f"jobs_func_{f}"] = func_mix[f]
            rows.append(row)
    return pd.DataFrame(rows)
