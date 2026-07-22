"""Evaluation math on hand-built fixtures: event-study alignment,
greedy precision/recall matching, Spearman against a known constant,
disclosed-revenue band arithmetic, scorecard-to-metrics reconciliation,
and a shuffle test that collapses rank correlation and precision."""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from evaluation import event_study, inflection_score, rank_quality, outcome_validation


def test_event_study_recovers_known_lead():
    quarters = ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2"]
    # jobs_pct jumps at 2023Q3 (index 2); composite/other sources flat
    scored = pd.DataFrame({
        "vendor_id": ["v1"] * 6, "quarter": quarters,
        "jobs_pct": [40, 40, 90, 90, 90, 90],
        "web_pct": [40, 40, 40, 40, 40, 40],
        "spend_pct": [40, 40, 40, 40, 40, 40],
    })
    inflections = pd.DataFrame([{"vendor_id": "v1", "quarter": "2023Q3", "type": "acceleration"}])
    raw = event_study.run(scored, inflections)
    jobs_rows = raw[(raw["source"] == "jobs")]
    assert jobs_rows.iloc[0]["detected"]
    assert jobs_rows.iloc[0]["detected_quarter"] == "2023Q3"
    assert jobs_rows.iloc[0]["lead_vs_regime_change"] == 0


def test_greedy_matching_hand_built():
    scored = pd.DataFrame([
        {"vendor_id": "v1", "quarter": "2023Q3", "tier": "A", "accel_flag": True, "stall_flag": False},
        {"vendor_id": "v1", "quarter": "2023Q4", "tier": "A", "accel_flag": False, "stall_flag": False},
        {"vendor_id": "v1", "quarter": "2024Q1", "tier": "A", "accel_flag": True, "stall_flag": False},
    ])
    events = pd.DataFrame([{"vendor_id": "v1", "quarter": "2023Q3", "type": "acceleration"}])
    flags_df, events_df = inflection_score.build_flags_and_events(scored, events)
    matched_flags, matched_events = inflection_score._greedy_match(flags_df, events_df, k=1)
    assert len(matched_events) == 1
    assert len(matched_flags) == 1


def test_spearman_matches_known_constant():
    composite = [10, 20, 30, 40, 50]
    growth = [0.5, 0.4, 0.3, 0.2, 0.1]  # perfectly inverse rank
    r, _ = spearmanr(composite, growth)
    assert abs(r - (-1.0)) < 1e-9


def test_disclosed_band_hand_arithmetic():
    level_bands = pd.DataFrame([
        {"vendor_id": "v1", "quarter": "2024Q1", "segment": "devtools",
         "arr_estimate_m": 5.0, "level_band": "3-10M", "level_method": "jobs"},
    ])
    disclosed = pd.DataFrame([{"vendor_id": "v1", "quarter": "2024Q2", "disclosed_revenue_m": 6.0}])
    events = pd.DataFrame([{"vendor_id": "v1", "event_type": "acquisition", "quarter": "2024Q1"}])
    summary, detail = outcome_validation.disclosed_acquisition_validation(level_bands, disclosed, events)
    assert summary["n"] == 1
    assert summary["band_hit_rate"] == 1.0
    expected_err = abs(np.log10(5.0) - np.log10(6.0))
    assert abs(summary["median_abs_log10_error"] - expected_err) < 1e-9


def test_scorecard_totals_reconcile_to_metrics(built):
    grid = built["metrics"]["inflection_precision_recall"]
    csv_grid = built["scorecard"]
    assert len(grid) == len(csv_grid)
    for r in grid:
        row = csv_grid[(csv_grid["k"] == r["k"]) & (csv_grid["type"] == r["type"])
                       & (csv_grid["tier"] == r["tier"])]
        assert len(row) == 1
        assert int(row.iloc[0]["n_flags"]) == r["n_flags"]
        assert int(row.iloc[0]["n_events"]) == r["n_events"]


def test_shuffle_collapses_rank_correlation():
    rng = np.random.default_rng(0)
    n = 200
    composite = rng.uniform(0, 100, n)
    growth = composite / 100.0 + rng.normal(0, 0.01, n)  # strongly correlated
    r_true, _ = spearmanr(composite, growth)
    assert r_true > 0.8

    shuffled = rng.permutation(composite)
    r_shuffled, _ = spearmanr(shuffled, growth)
    assert abs(r_shuffled) < 0.15
