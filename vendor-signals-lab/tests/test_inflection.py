"""Inflection constants match the frozen freeze, and flags are
reproducible purely from the committed health_index.csv columns."""

from estimation import inflection


def test_frozen_constants():
    assert inflection.ACCEL_DELTA == 15.0
    assert inflection.ACCEL_FLOOR == 55.0
    assert inflection.STALL_DELTA == -15.0
    assert inflection.STALL_CEILING == 45.0
    assert inflection.MIN_PRIOR_QUARTERS == 2


def test_flags_reproducible_from_health_index(built):
    h = built["health"]
    recomputed = inflection.add_flags(h[["vendor_id", "quarter", "composite"]])
    merged = h.merge(recomputed, on=["vendor_id", "quarter"], suffixes=("_committed", "_recomputed"))
    assert (merged["accel_flag_committed"] == merged["accel_flag_recomputed"]).all()
    assert (merged["stall_flag_committed"] == merged["stall_flag_recomputed"]).all()


def test_sensitivity_strip_monotonic_precision_recall():
    """A tighter delta threshold should never flag more than a looser
    one, on the same composite series."""
    import pandas as pd
    df = pd.DataFrame({
        "vendor_id": ["v1"] * 6,
        "quarter": ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2"],
        "composite": [40, 45, 60, 62, 40, 20],
    })
    n_flags = {}
    for delta in (10, 15, 20):
        flagged = inflection.add_flags(df, delta=delta, floor=50, stall_delta=-delta, ceiling=50)
        n_flags[delta] = int(flagged["accel_flag"].sum() + flagged["stall_flag"].sum())
    assert n_flags[10] >= n_flags[15] >= n_flags[20]


def test_threshold_sensitivity_table_reproduces_readme_numbers(built):
    """README's post-freeze threshold-sensitivity table
    (outputs/robustness_seed_check.md) is reproducible from the
    committed health_index.csv and data/truth/inflections.csv using
    robustness_check.threshold_sensitivity with floor/ceiling held fixed
    at the frozen 55/45. This is the mechanical tether the numbers
    otherwise lack."""
    import robustness_check

    health = built["health"]
    inflections = built["truth_inflections"]
    result = robustness_check.threshold_sensitivity(health, inflections).set_index("delta")

    expected = {
        10.0: {"n_flags": 2184, "precision": 10.5, "recall": 83.3},
        15.0: {"n_flags": 1736, "precision": 12.5, "recall": 78.6},
        20.0: {"n_flags": 1317, "precision": 14.2, "recall": 67.8},
    }
    for delta, exp in expected.items():
        row = result.loc[delta]
        assert int(row["n_flags"]) == exp["n_flags"]
        assert abs(100 * row["precision"] - exp["precision"]) < 0.1
        assert abs(100 * row["recall"] - exp["recall"]) < 0.1
    # tighter delta never flags more than a looser one, population-pooled
    assert result.loc[10.0, "n_flags"] >= result.loc[15.0, "n_flags"] >= result.loc[20.0, "n_flags"]
