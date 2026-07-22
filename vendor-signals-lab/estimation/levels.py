"""Half-decade ARR bands: the honest answer to "how big is this vendor",
which is never a point estimate here. Fixed, deliberately crude fallback
chain, cheapest signal first available: spend (highest fidelity where
present) > jobs (tracked) > web (last resort). Every constant below is a
round, stated guess, not fit to anything, and not shared with (or
derived from) simulation/params.py, which this module may not import.
"""

import numpy as np
import pandas as pd

BANDS = [
    ("<1M", 0, 1e6),
    ("1-3M", 1e6, 3e6),
    ("3-10M", 3e6, 10e6),
    ("10-30M", 10e6, 30e6),
    ("30-100M", 30e6, 100e6),
    (">100M", 100e6, float("inf")),
]

# Not a size band: stamped when zero sources are observed that
# vendor-quarter, so a genuine "we saw nothing" is never rendered as the
# same label as a genuinely observed small vendor.
NO_DATA_BAND = "no_data"

ASSUMED_PANEL_SHARE = 0.02             # one number for the whole world
ASSUMED_EMPLOYEES_PER_OPEN_ROLE = 12.0
ASSUMED_REV_PER_EMPLOYEE = {
    "devtools": 220_000, "data_infrastructure": 200_000,
    "ai_applications": 250_000, "security": 230_000, "vertical_saas": 200_000,
}
ASSUMED_DOLLARS_PER_VISIT_ANNUAL = {
    "devtools": 32.0, "data_infrastructure": 40.0, "ai_applications": 24.0,
    "security": 48.0, "vertical_saas": 28.0,
}


def band_for(value: float) -> str:
    for name, lo, hi in BANDS:
        if lo <= value < hi:
            return name
    return BANDS[-1][0]


def estimate_row(row) -> tuple:
    """Returns (arr_estimate_dollars, band, method)."""
    seg = row["segment"]
    if row["spend_status"] == "present" and row.get("spend_amount", 0) > 0:
        est = row["spend_amount"] * 4.0 / ASSUMED_PANEL_SHARE
        return est, band_for(est), "spend"
    if row["jobs_status"] in ("tracked_active", "tracked_zero"):
        implied_hc = row.get("jobs_new_postings", 0) * ASSUMED_EMPLOYEES_PER_OPEN_ROLE
        est = implied_hc * ASSUMED_REV_PER_EMPLOYEE.get(seg, 220_000)
        return est, band_for(est), "jobs"
    if row["web_status"] == "present":
        est = row.get("web_visits", 0) * 4.0 * ASSUMED_DOLLARS_PER_VISIT_ANNUAL.get(seg, 30.0)
        return est, band_for(est), "web"
    # Nothing observed this vendor-quarter (no spend, no tracked jobs
    # activity, no web presence). This is not evidence of a small
    # vendor: it is the absence of any evidence at all, so it is
    # stamped with its own band rather than falling into "<1M" and
    # reading identically to a genuinely observed small vendor.
    return float("nan"), NO_DATA_BAND, "none"


def build_level_bands(coverage_matrix_with_amounts: pd.DataFrame) -> pd.DataFrame:
    df = coverage_matrix_with_amounts.copy()
    ests, bands, methods = [], [], []
    for _, row in df.iterrows():
        e, b, m = estimate_row(row)
        ests.append(e)
        bands.append(b)
        methods.append(m)
    df["arr_estimate_m"] = np.array(ests) / 1e6
    df["level_band"] = bands
    df["level_method"] = methods
    return df[["vendor_id", "quarter", "segment", "arr_estimate_m", "level_band", "level_method"]]
