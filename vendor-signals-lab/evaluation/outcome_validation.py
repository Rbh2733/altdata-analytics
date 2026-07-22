"""Outcome validation: does the composite trajectory look right ahead of
shutdowns and funding rounds, and how do the level bands do against the
sparse disclosed acquisition revenues. This is the centerpiece's least
flattering table by design: outcome events are impure by construction
(strugglers raise on runway pressure too), and levels are bands, not
points, for a reason this section makes concrete.
"""

import numpy as np
import pandas as pd

import config

BAND_ORDER = ["<1M", "1-3M", "3-10M", "10-30M", "30-100M", ">100M"]


def _band_index(band):
    return BAND_ORDER.index(band) if band in BAND_ORDER else None


def shutdown_validation(scored_df: pd.DataFrame, outcome_events: pd.DataFrame):
    shutdowns = outcome_events[outcome_events["event_type"] == "shutdown"]
    comp = scored_df.set_index(["vendor_id", "quarter"])["composite"]
    pop_median_by_q = scored_df.groupby("quarter")["composite"].median()

    detail = []
    bottom_q_hits = 0
    n_scored_t2 = 0
    above_50_at_t1 = []
    for _, ev in shutdowns.iterrows():
        vid, q = ev["vendor_id"], ev["quarter"]
        qi = config.quarter_index(q)
        t1_i, t2_i = qi - 1, qi - 2
        t1 = config.QUARTERS[t1_i] if t1_i >= 0 else None
        t2 = config.QUARTERS[t2_i] if t2_i >= 0 else None
        c_t1 = comp.get((vid, t1)) if t1 else None
        c_t2 = comp.get((vid, t2)) if t2 else None
        if t2 and c_t2 is not None and not pd.isna(c_t2):
            n_scored_t2 += 1
            q1_cut = scored_df[scored_df["quarter"] == t2]["composite"].quantile(0.25)
            if c_t2 <= q1_cut:
                bottom_q_hits += 1
        if t1 and c_t1 is not None and not pd.isna(c_t1) and c_t1 > 50:
            tier_at_t1 = scored_df[(scored_df["vendor_id"] == vid)
                                    & (scored_df["quarter"] == t1)]["tier"]
            above_50_at_t1.append({"vendor_id": vid, "shutdown_quarter": q,
                                    "composite_t1": c_t1,
                                    "tier": tier_at_t1.iloc[0] if len(tier_at_t1) else None})
        detail.append({"vendor_id": vid, "shutdown_quarter": q,
                       "composite_t1": c_t1, "composite_t2": c_t2})

    detail_df = pd.DataFrame(detail)
    med_t1 = detail_df["composite_t1"].median() if len(detail_df) else float("nan")
    overall_median = scored_df["composite"].median()
    return {
        "n_shutdowns": len(shutdowns),
        "n_scored_at_t2": n_scored_t2,
        "bottom_quartile_share_at_t2": bottom_q_hits / n_scored_t2 if n_scored_t2 else float("nan"),
        "median_composite_at_t1": med_t1,
        "population_median_composite": overall_median,
        "above_50_at_t1": above_50_at_t1,
        "detail": detail_df,
    }


def funding_validation(scored_df: pd.DataFrame, outcome_events: pd.DataFrame):
    fundings = outcome_events[outcome_events["event_type"] == "funding"]
    comp = scored_df.set_index(["vendor_id", "quarter"])["composite"]
    vals = []
    for _, ev in fundings.iterrows():
        vid, q = ev["vendor_id"], ev["quarter"]
        qi = config.quarter_index(q)
        if qi - 1 < 0:
            continue
        t1 = config.QUARTERS[qi - 1]
        c = comp.get((vid, t1))
        if c is not None and not pd.isna(c):
            vals.append(c)
    return {
        "n_funding_events": len(fundings),
        "n_scored": len(vals),
        "median_composite_before_round": float(np.median(vals)) if vals else float("nan"),
        "population_median_composite": scored_df["composite"].median(),
    }


def disclosed_acquisition_validation(level_bands: pd.DataFrame, disclosed: pd.DataFrame,
                                      outcome_events: pd.DataFrame):
    """Graded at the acquisition quarter itself, not the (later) disclosure
    quarter: exhaust darkens the quarter after acquisition by design (see
    simulation/outcomes.py), which is exactly the disclosure quarter, so
    grading there would compare the disclosed figure against a
    guaranteed-empty read. The acquisition quarter is the shop's last
    live estimate before the company goes dark, which is the fair
    comparison point."""
    acq = outcome_events[outcome_events["event_type"] == "acquisition"][["vendor_id", "quarter"]]
    acq = acq.rename(columns={"quarter": "acq_quarter"})
    disclosed = disclosed.merge(acq, on="vendor_id", how="left")
    rows = []
    for _, d in disclosed.iterrows():
        vid, disc_q, disc_rev = d["vendor_id"], d["quarter"], d["disclosed_revenue_m"]
        est_q = d["acq_quarter"] if pd.notna(d["acq_quarter"]) else disc_q
        lb = level_bands[(level_bands["vendor_id"] == vid) & (level_bands["quarter"] == est_q)]
        if lb.empty:
            continue
        est_band = lb.iloc[0]["level_band"]
        est_arr = lb.iloc[0]["arr_estimate_m"]
        if pd.isna(est_arr):
            # No source observed this vendor-quarter (level_method
            # "none"): nothing to grade, and no fabricated level.
            continue
        true_band = None
        for name, lo, hi in [("<1M", 0, 1), ("1-3M", 1, 3), ("3-10M", 3, 10),
                              ("10-30M", 10, 30), ("30-100M", 30, 100), (">100M", 100, float("inf"))]:
            if lo <= disc_rev < hi:
                true_band = name
                break
        band_hit = est_band == true_band
        within_one = False
        ei, ti = _band_index(est_band), _band_index(true_band)
        if ei is not None and ti is not None:
            within_one = abs(ei - ti) <= 1
        log_err = abs(np.log10(max(est_arr, 0.01)) - np.log10(max(disc_rev, 0.01)))
        rows.append({"vendor_id": vid, "quarter": disc_q, "estimated_at_quarter": est_q,
                     "disclosed_revenue_m": disc_rev,
                     "estimated_arr_m": est_arr, "estimated_band": est_band,
                     "true_band": true_band, "band_hit": band_hit,
                     "within_one_band": within_one, "abs_log10_error": log_err})
    df = pd.DataFrame(rows)
    summary = {
        "n": len(df),
        "band_hit_rate": df["band_hit"].mean() if len(df) else float("nan"),
        "within_one_band_share": df["within_one_band"].mean() if len(df) else float("nan"),
        "median_abs_log10_error": df["abs_log10_error"].median() if len(df) else float("nan"),
    }
    return summary, df
