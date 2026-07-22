"""Acceleration/stall flags. Frozen thresholds, one-line rationale each:

- +/-15 points: roughly a full segment-quintile move in the composite
  percentile, big enough that "the vendor changed lanes" is a fair read.
- 55 / 45 floors: a flag additionally requires the vendor to have
  crossed to the healthy/unhealthy side of the midpoint, not just moved
  15 points while still near it.
- 2 prior quarters minimum: one prior point cannot establish a "before"
  level to move away from.

A post-freeze sensitivity strip at 10/15/20 is reported in the README to
show how precision/recall degrade around this choice.
"""

import config

ACCEL_DELTA = 15.0
ACCEL_FLOOR = 55.0
STALL_DELTA = -15.0
STALL_CEILING = 45.0
MIN_PRIOR_QUARTERS = 2


def add_flags(composite_df, delta=ACCEL_DELTA, floor=ACCEL_FLOOR,
              stall_delta=STALL_DELTA, ceiling=STALL_CEILING):
    df = composite_df.sort_values(["vendor_id", "quarter"]).copy()
    df["accel_flag"] = False
    df["stall_flag"] = False
    df["composite_delta"] = None

    for vid, grp in df.groupby("vendor_id", sort=False):
        idxs = grp.index.tolist()
        comps = grp["composite"].tolist()
        for pos, idx in enumerate(idxs):
            if pos < MIN_PRIOR_QUARTERS:
                continue
            prior_mean = (comps[pos - 2] + comps[pos - 1]) / 2.0
            d = comps[pos] - prior_mean
            df.loc[idx, "composite_delta"] = d
            if d >= delta and comps[pos] >= floor:
                df.loc[idx, "accel_flag"] = True
            elif d <= stall_delta and comps[pos] <= ceiling:
                df.loc[idx, "stall_flag"] = True
    return df
