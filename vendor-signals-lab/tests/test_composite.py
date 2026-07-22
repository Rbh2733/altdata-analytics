"""Composite bounds, weight renormalization, missing-source handling,
within-segment-quarter percentiles, and tier-C-only shrinkage."""

import pandas as pd

from estimation import composite


def test_composite_bounds(built):
    h = built["health"]
    assert h["composite"].min() >= 0.0 - 1e-6
    assert h["composite"].max() <= 100.0 + 1e-6


def test_shrinkage_applied_only_at_tier_c():
    df = pd.DataFrame({
        "segment": ["s"] * 4, "quarter": ["2023Q3"] * 4,
        "tier": ["A", "B", "C", "C"],
        "jobs_pct": [90.0, 90.0, 90.0, None],
        "web_pct": [90.0, None, 90.0, None],
        "spend_pct": [90.0, 90.0, None, None],
    })
    withcomp = composite.build_composite(df)
    a_row = withcomp[withcomp["tier"] == "A"].iloc[0]
    c_row = withcomp[withcomp["tier"] == "C"].iloc[0]
    assert a_row["composite"] == a_row["composite_raw"]
    assert c_row["composite"] != c_row["composite_raw"]
    assert c_row["composite"] == 50.0 + 0.5 * (c_row["composite_raw"] - 50.0)


def test_missing_source_contributes_zero_weight():
    df = pd.DataFrame({
        "segment": ["s", "s"], "quarter": ["2023Q3", "2023Q3"], "tier": ["A", "A"],
        "jobs_pct": [80.0, 20.0], "web_pct": [None, None], "spend_pct": [None, None],
    })
    withcomp = composite.build_composite(df)
    # with only jobs present, composite should equal the jobs percentile
    assert abs(withcomp.iloc[0]["composite"] - 80.0) < 1e-9
    assert abs(withcomp.iloc[1]["composite"] - 20.0) < 1e-9


def test_percentiles_within_segment_quarter_over_present_only():
    merged = pd.DataFrame({
        "vendor_id": ["v1", "v2", "v3"], "segment": ["s", "s", "s"],
        "quarter": ["2023Q3"] * 3,
        "jobs_status": ["tracked_active", "tracked_active", "untracked"],
        "web_status": ["present", "present", "present"],
        "spend_presence": ["absent", "absent", "absent"],
        "jobs_growth": [0.1, 0.5, 0.9], "web_growth": [0.1, 0.5, 0.9],
        "spend_growth": [None, None, None],
    })
    withpct = composite.add_percentiles(merged)
    # v3 is untracked (jobs absent) so its jobs_growth must not enter the
    # ranking even though a value exists in the column
    ranked = withpct.dropna(subset=["jobs_pct"])
    assert set(ranked["vendor_id"]) == {"v1", "v2"}


def test_every_row_carries_a_tier_no_default_a(built):
    h = built["health"]
    assert h["tier"].isin(["A", "B", "C"]).all()
    assert set(h["tier"].unique()) == {"A", "B", "C"}


def test_equal_weight_check_reproduces_readme_numbers(built):
    """README's post-freeze equal-weights composite check
    (outputs/robustness_seed_check.md) is reproducible from the
    committed health_index.csv and data/truth/truth_financials.csv via
    robustness_check.equal_weight_composite_check. This is the
    mechanical tether the number otherwise lacks."""
    import robustness_check

    health = built["health"]
    truth_financials = built["truth_financials"]
    tier_gradient = robustness_check.equal_weight_composite_check(health, truth_financials)

    assert abs(tier_gradient["A"] - 0.720) < 0.005
    assert abs(tier_gradient["B"] - 0.493) < 0.005
    assert abs(tier_gradient["C"] - 0.312) < 0.005
    # SOURCE_WEIGHTS must be restored to the frozen values afterward
    from estimation import composite
    assert composite.SOURCE_WEIGHTS == {"jobs": 0.35, "web": 0.20, "spend": 0.45}
