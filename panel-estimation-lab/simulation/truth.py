"""True quarterly KPIs, computed by exact aggregation of population state.

Definitions (mirrored by the estimation layer's target definitions):
- revenue: all charges and purchases attributed to the company in the quarter.
- actives: subscriptions: subscribers at quarter end (after that month's
  churn); e-commerce: trailing-12-month purchasers as of quarter end.
- gross_adds: subscriptions: adoption events in the quarter (winbacks
  included); e-commerce: newly active vs the prior quarter end.
- churn_rate: subscriptions: churn events in the quarter divided by
  actives at the prior quarter end; e-commerce: share of prior-quarter
  actives no longer active.
- arpu: quarterly revenue / actives.
- market_share: company revenue share of the six-company total, percent.

The identity actives_t = actives_{t-1} + gross_adds - churned holds
exactly by construction (a test verifies it).
"""

import numpy as np
import pandas as pd

import config
from simulation import params


def build_truth(subs, ecom, pinefort_purchases):
    rows = []
    rev = {}  # (co, q_idx) -> revenue
    for co in params.COMPANIES:
        for qi in range(12):
            months = [3 * qi + 1, 3 * qi + 2, 3 * qi + 3]
            if co in params.SUB_COMPANIES:
                r = sum(subs[co]["revenue_m"][m - 1] for m in months)
                if co == "Pinefort":
                    r += sum(pinefort_purchases["revenue_m"][m - 1] for m in months)
            else:
                r = sum(ecom[co]["revenue_m"][m - 1] for m in months)
            rev[(co, qi)] = r

    for co in params.COMPANIES:
        for qi in range(12):
            months = [3 * qi + 1, 3 * qi + 2, 3 * qi + 3]
            r = rev[(co, qi)]
            if co in params.SUB_COMPANIES:
                s = subs[co]
                actives = int(s["end_m"][months[-1] - 1])
                prev = int(s["end_m"][months[0] - 2]) if qi > 0 else s["baseline_end"]
                adds = int(sum(s["adopt_m"][m - 1] for m in months))
                churned = int(sum(s["churn_m"][m - 1] for m in months))
            else:
                e = ecom[co]
                actives = int(e["actives_q"][qi])
                prev = int(e["actives_q"][qi - 1]) if qi > 0 else e["baseline"]
                adds = int(e["adds_q"][qi])
                churned = int(e["churn_q"][qi])
            churn_rate = churned / prev if prev > 0 else 0.0
            arpu = r / actives if actives > 0 else 0.0
            total_rev = sum(rev[(c, qi)] for c in params.COMPANIES)
            share = 100.0 * r / total_rev
            rows.append({
                "company": co,
                "quarter": config.QUARTERS[qi],
                "revenue": round(r, 2),
                "actives": actives,
                "gross_adds": adds,
                "churned": churned,
                "prior_actives": prev,
                "churn_rate": round(churn_rate, 6),
                "arpu": round(arpu, 4),
                "market_share": round(share, 4),
            })
    df = pd.DataFrame(rows)
    return df.sort_values(["company", "quarter"]).reset_index(drop=True)


def build_reported(truth):
    """Reported actuals: revenue and actives only, disclosure-rounded
    (revenue to the nearest 0.1M, actives to the nearest thousand).
    Companies do not report churn or ARPU; the shop estimates what is
    not reported."""
    rep = truth[["company", "quarter", "revenue", "actives"]].copy()
    rep["revenue"] = (np.round(rep["revenue"] / 100_000.0) * 100_000.0).round(1)
    rep["actives"] = (np.round(rep["actives"] / 1_000.0) * 1_000.0).astype(np.int64)
    return rep.sort_values(["company", "quarter"]).reset_index(drop=True)
