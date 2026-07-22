"""Lead-lag event study: how far ahead of a truth inflection does each
source family's own percentile series cross the same +/-15-point rule
the composite flagger uses. One rule everywhere, no per-source tuning.

The window around each truth inflection (t0) is t0-4 .. t0+4, truncated
asymmetrically at the edges of the 12-quarter calendar; this is stated
explicitly rather than silently dropping edge events.

Disclosed cap: `_source_delta_series` needs two prior quarters of history
before it will compute a delta at all, so the earliest position in the
window that can ever register a `first_cross` is t0-2, not t0-4. This
silently caps the maximum measurable `lead_vs_regime_change` at 2
quarters regardless of the nominal 4-quarter WINDOW_BACK; a genuinely
longer lead would be truncated to 2 without any warning in the output.
In this run the engineered leads (jobs ~2, web/spend ~1) sit at or under
that cap, so it is not visibly binding here, but it would bind under a
different parameterization.
"""

import numpy as np
import pandas as pd

import config
from estimation.inflection import ACCEL_DELTA, STALL_DELTA

WINDOW_BACK = 4
WINDOW_FWD = 4


def _source_delta_series(pct_series: dict, quarters: list):
    """pct_series: {quarter: value or nan}. Returns {quarter: delta} using
    the same trailing-2-quarter-mean rule as the composite flagger."""
    deltas = {}
    for i, q in enumerate(quarters):
        if i < 2:
            continue
        a, b, c = pct_series.get(quarters[i - 2]), pct_series.get(quarters[i - 1]), pct_series.get(q)
        if a is None or b is None or c is None or any(pd.isna(x) for x in (a, b, c)):
            continue
        deltas[q] = c - (a + b) / 2.0
    return deltas


def run(scored_df: pd.DataFrame, inflections_df: pd.DataFrame) -> pd.DataFrame:
    """scored_df: the full composite-enriched estimation output (one row
    per vendor-quarter) with jobs_pct/web_pct/spend_pct columns.
    inflections_df: data/truth/inflections.csv."""
    sources = {"jobs": "jobs_pct", "web": "web_pct", "spend": "spend_pct"}
    by_vendor = {vid: g.set_index("quarter") for vid, g in scored_df.groupby("vendor_id")}

    rows = []
    for _, ev in inflections_df.iterrows():
        vid, t0, etype = ev["vendor_id"], ev["quarter"], ev["type"]
        if vid not in by_vendor:
            continue
        vdf = by_vendor[vid]
        idx0 = config.quarter_index(t0)
        lo = max(0, idx0 - WINDOW_BACK)
        hi = min(config.N_QUARTERS - 1, idx0 + WINDOW_FWD)
        window_quarters = config.QUARTERS[lo:hi + 1]

        for src, col in sources.items():
            if col not in vdf.columns:
                continue
            pct_series = {q: (vdf.loc[q, col] if q in vdf.index else np.nan) for q in window_quarters}
            present = any(pd.notna(v) for v in pct_series.values())
            deltas = _source_delta_series(pct_series, window_quarters)
            threshold = ACCEL_DELTA if etype == "acceleration" else STALL_DELTA
            first_cross = None
            for q in window_quarters:
                if q not in deltas:
                    continue
                d = deltas[q]
                hit = (d >= threshold) if etype == "acceleration" else (d <= threshold)
                if hit:
                    first_cross = q
                    break
            lead_t0 = (idx0 - config.quarter_index(first_cross)) if first_cross else None
            lead_rev = (idx0 + 2 - config.quarter_index(first_cross)) if first_cross else None
            rows.append({
                "vendor_id": vid, "event_quarter": t0, "event_type": etype,
                "source": src, "present": present, "detected": first_cross is not None,
                "detected_quarter": first_cross,
                "lead_vs_regime_change": lead_t0, "lead_vs_revenue_realization": lead_rev,
            })
    return pd.DataFrame(rows)


def summarize(leadlag_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (src, etype), g in leadlag_df.groupby(["source", "event_type"]):
        present = g[g["present"]]
        n_present = len(present)
        n_events = len(g)
        detected = present[present["detected"]]
        n_detected = len(detected)
        det_rate = n_detected / n_present if n_present else float("nan")
        med_lead_t0 = detected["lead_vs_regime_change"].median() if n_detected else float("nan")
        med_lead_rev = detected["lead_vs_revenue_realization"].median() if n_detected else float("nan")
        q1 = detected["lead_vs_regime_change"].quantile(0.25) if n_detected else float("nan")
        q3 = detected["lead_vs_regime_change"].quantile(0.75) if n_detected else float("nan")
        rows.append({
            "source": src, "event_type": etype, "n_events": n_events,
            "n_present": n_present, "n_detected": n_detected,
            "detection_rate": det_rate, "median_lead_vs_regime_change": med_lead_t0,
            "iqr_lo": q1, "iqr_hi": q3,
            "median_lead_vs_revenue_realization": med_lead_rev,
        })
    return pd.DataFrame(rows).sort_values(["source", "event_type"]).reset_index(drop=True)
