"""All declared outputs exist and are nonempty, and metrics.json carries
the keys the README's numbers are sourced from (the mechanical
prose-to-code tether: every headline number in the README traces to a
key in this file, not a hand-typed value)."""

import json

EXPECTED_OUTPUTS = [
    "coverage_matrix.csv", "health_index.csv", "inflections_flagged.csv",
    "level_bands.csv", "naive_vs_qa.csv", "qa_report.md", "tagger_report.md",
    "scorecard.md", "scorecard.csv", "leadlag.csv", "metrics.json",
]

EXPECTED_METRICS_KEYS = [
    "n_vendors", "n_scored_quarters", "tier_mix", "rank_quality_by_tier",
    "rank_quality_blended", "leadlag_summary", "inflection_precision_recall",
    "shutdown_validation", "funding_validation", "disclosed_acquisition_validation",
]


def test_declared_outputs_exist_and_nonempty(built):
    for name in EXPECTED_OUTPUTS:
        p = built["out"] / name
        assert p.exists(), f"missing output {name}"
        assert p.stat().st_size > 0, f"empty output {name}"


def test_metrics_json_has_expected_keys(built):
    with open(built["out"] / "metrics.json", encoding="utf-8") as fh:
        m = json.load(fh)
    for k in EXPECTED_METRICS_KEYS:
        assert k in m, f"metrics.json missing key {k}"


def test_metrics_json_tier_gradient_present(built):
    m = built["metrics"]
    grad = m["rank_quality_by_tier"]
    assert set(grad.keys()) >= {"A", "B", "C"}


def test_data_directories_populated(built):
    for sub in ("exhaust", "public", "truth"):
        d = built["root"] / "data" / sub
        files = list(d.glob("*.csv"))
        assert files, f"data/{sub} has no committed CSVs"
