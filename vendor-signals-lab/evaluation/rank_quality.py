"""Rank quality: Spearman correlation between the composite and true
forward ARR growth (quarter t to t+1), computed within each scored
quarter and summarized as the median across quarters, by tier and by
segment.

Spearman, not Pearson: the composite makes an ordinal claim ("this
vendor looks healthier than that one this quarter"), not a levels claim,
so the ordinal statistic is the honest one to score it with, and it is
familiar at this sample size.

The tier gradient (A >> B >> C) is the thesis of this whole lab: a
single blended correlation across all tiers would launder tier-C
ignorance through tier-A precision, so the blended number is reported
only for reference, never as the headline.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import config

MIN_N_FOR_CORR = 5


def _fwd_growth_map(truth_financials: pd.DataFrame, q: str, nq: str):
    t = truth_financials[truth_financials["quarter"].isin([q, nq])]
    piv = t.pivot(index="vendor_id", columns="quarter", values="arr_m")
    if q not in piv.columns or nq not in piv.columns:
        return {}
    piv = piv.dropna(subset=[q, nq])
    growth = (piv[nq] - piv[q]) / piv[q].replace(0, np.nan)
    return growth.to_dict()


def compute(scored_df: pd.DataFrame, truth_financials: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for q in config.SCORED_QUARTERS:
        qi = config.quarter_index(q)
        if qi + 1 >= config.N_QUARTERS:
            continue
        nq = config.QUARTERS[qi + 1]
        fwd = _fwd_growth_map(truth_financials, q, nq)
        sub = scored_df[scored_df["quarter"] == q][
            ["vendor_id", "composite", "tier", "segment"]].copy()
        sub["fwd_growth"] = sub["vendor_id"].map(fwd)
        sub = sub.dropna(subset=["fwd_growth"])

        def _corr(frame):
            if len(frame) < MIN_N_FOR_CORR:
                return float("nan"), len(frame)
            r, _ = spearmanr(frame["composite"], frame["fwd_growth"])
            return r, len(frame)

        r, n = _corr(sub)
        rows.append({"quarter": q, "cut": "blended", "key": "ALL", "n": n, "spearman": r})
        for tier in ("A", "B", "C"):
            r, n = _corr(sub[sub["tier"] == tier])
            rows.append({"quarter": q, "cut": "tier", "key": tier, "n": n, "spearman": r})
        for seg in config.SEGMENTS:
            r, n = _corr(sub[sub["segment"] == seg])
            rows.append({"quarter": q, "cut": "segment", "key": seg, "n": n, "spearman": r})
    return pd.DataFrame(rows)


def summarize(rank_df: pd.DataFrame) -> pd.DataFrame:
    g = rank_df.groupby(["cut", "key"])["spearman"].median().reset_index()
    g = g.rename(columns={"spearman": "median_spearman"})
    n_quarters = rank_df.groupby(["cut", "key"]).size().reset_index(name="n_quarters")
    return g.merge(n_quarters, on=["cut", "key"])
