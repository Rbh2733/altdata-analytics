"""Reconciliation math, hierarchy resolution, and every planted case."""

import pytest

from market_data_pipeline.models import MetricObservation, resolution_order
from market_data_pipeline.pipeline import collect_observations, make_clients
from market_data_pipeline.reconcile import (
    classify,
    looks_like_scale_mismatch,
    reconcile,
    relative_disagreement_pct,
    spread_of,
    summarize,
)


def obs(source, value, period_end="2025-12-31", metric="revenue",
        period="FY2025", ticker="TEST"):
    return MetricObservation(
        ticker=ticker, source=source, metric=metric, period=period,
        period_end=period_end, value=value, unit="USD", as_of=period_end,
    )


# ---------------------------------------------------------------------------
# Spread and classification math
# ---------------------------------------------------------------------------


def test_spread_and_relative_disagreement():
    values = [100.0, 104.0, 98.0]
    assert spread_of(values) == 6.0
    assert relative_disagreement_pct(values) == pytest.approx(6.0)  # /100 median


def test_relative_disagreement_single_value_is_zero():
    assert relative_disagreement_pct([42.0]) == 0.0


def test_scale_mismatch_detects_powers_of_ten():
    assert looks_like_scale_mismatch([2_000.0, 2_000_000.0]) == 1_000.0
    assert looks_like_scale_mismatch([5.0, 495.0]) == 100.0  # within 5 percent
    assert looks_like_scale_mismatch([100.0, 104.0]) == 0.0
    assert looks_like_scale_mismatch([-3_000.0, -3.0]) == 1_000.0


def test_scale_mismatch_ignores_zero_and_mixed_signs():
    assert looks_like_scale_mismatch([0.0, 1_000.0]) == 0.0
    assert looks_like_scale_mismatch([-1_000.0, 1.0]) == 0.0


def test_classify_thresholds():
    ends = ["2025-12-31", "2025-12-31"]
    assert classify([100.0, 100.3], ends)[0] == "agreement"
    assert classify([100.0, 101.5], ends)[0] == "minor_divergence"
    assert classify([100.0, 106.0], ends)[0] == "material_divergence"
    assert classify([100.0], ["2025-12-31"])[0] == "single_source"


def test_classify_period_misalignment_beats_value_grading():
    cls, note = classify([100.0, 101.5], ["2025-12-31", "2026-01-31"])
    assert cls == "period_misalignment"
    assert "31 days" in note


def test_classify_scale_beats_period():
    cls, _ = classify([100.0, 100_000.0], ["2025-12-31", "2026-01-31"])
    assert cls == "unit_scale_mismatch"


# ---------------------------------------------------------------------------
# Hierarchy resolution
# ---------------------------------------------------------------------------


def test_resolution_order_regulatory_first_then_alphabetical():
    assert resolution_order(["polygon", "edgar", "fmp"]) == \
        ["edgar", "fmp", "polygon"]
    assert resolution_order(["polygon", "fmp"]) == ["fmp", "polygon"]


def test_reconcile_resolves_to_regulatory_source():
    groups = reconcile([
        obs("polygon", 101.0), obs("edgar", 100.0), obs("fmp", 102.0),
    ])
    assert len(groups) == 1
    g = groups[0]
    assert g.resolved_source == "edgar"
    assert g.resolved_value == 100.0
    assert g.regulatory_anchor is True
    assert g.resolved_tier == "regulatory"


def test_reconcile_without_regulatory_source_flags_anchor():
    groups = reconcile([obs("polygon", 101.0), obs("fmp", 102.0)])
    g = groups[0]
    assert g.resolved_source == "fmp"
    assert g.regulatory_anchor is False
    assert g.resolved_tier == "commercial"


def test_duplicate_source_in_group_fails_loudly():
    with pytest.raises(ValueError):
        reconcile([obs("fmp", 100.0), obs("fmp", 101.0)])


# ---------------------------------------------------------------------------
# Every planted case in the committed fixtures must surface
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def offline_reconciled():
    clients = make_clients()
    tickers = clients[0].fixture_tickers()
    observations = collect_observations(clients, tickers, live=False)
    reconciled = reconcile(observations)
    return {(g.ticker, g.metric, g.period): g for g in reconciled}


def test_planted_unit_scale_mismatch(offline_reconciled):
    g = offline_reconciled[("ONFD", "revenue", "FY2025")]
    assert g.classification == "unit_scale_mismatch"
    assert g.values["fmp"] == 2_847_300
    assert g.resolved_value == 2_847_300_000
    assert g.resolved_source == "edgar"
    assert "1,000x scale factor" in g.note


def test_planted_period_misalignment_covers_every_nmbw_group(offline_reconciled):
    nmbw = [g for k, g in offline_reconciled.items() if k[0] == "NMBW"]
    assert len(nmbw) == 10
    assert all(g.classification == "period_misalignment" for g in nmbw)
    g = offline_reconciled[("NMBW", "revenue", "FY2025")]
    assert g.period_ends["edgar"] == "2026-01-31"
    assert g.period_ends["fmp"] == "2025-12-31"


def test_planted_restatement_divergence(offline_reconciled):
    g = offline_reconciled[("QNTB", "revenue", "FY2024")]
    assert g.classification == "material_divergence"
    assert g.values["edgar"] == 1_412_400_000  # restated, latest filed wins
    assert g.values["fmp"] == 1_538_200_000    # stale pre-restatement value
    assert g.resolved_value == 1_412_400_000
    assert g.rel_disagreement_pct == pytest.approx(8.906, abs=0.01)


def test_planted_missing_metric_single_source(offline_reconciled):
    g = offline_reconciled[("CNDP", "operating_cash_flow", "FY2025")]
    assert g.classification == "single_source"
    assert g.n_sources == 1
    assert g.resolved_source == "edgar"


def test_planted_edgar_tag_gap_loses_regulatory_anchor(offline_reconciled):
    g = offline_reconciled[("TSSL", "revenue", "FY2024")]
    assert "edgar" not in g.values
    assert g.resolved_source == "fmp"
    assert g.regulatory_anchor is False


def test_planted_minor_divergences(offline_reconciled):
    for key in [
        ("MRHW", "net_income", "FY2025"),
        ("TSSL", "revenue", "FY2025"),
        ("PLXF", "operating_cash_flow", "FY2025"),
    ]:
        assert offline_reconciled[key].classification == "minor_divergence", key


def test_sub_tolerance_difference_stays_agreement(offline_reconciled):
    # ARBL total assets differ by under 0.1 percent across sources; the
    # tolerance band must absorb that instead of flagging it.
    g = offline_reconciled[("ARBL", "total_assets", "FY2025")]
    assert g.classification == "agreement"
    assert 0.0 < g.rel_disagreement_pct < 0.5


def test_summary_tallies(offline_reconciled):
    reconciled = list(offline_reconciled.values())
    # summarize needs observations only for source names and counts.
    clients = make_clients()
    observations = collect_observations(
        clients, clients[0].fixture_tickers(), live=False)
    s = summarize(reconciled, observations)
    assert s["groups"] == 100
    assert s["observations"] == 296
    assert s["classification"]["agreement"] == 84
    assert s["classification"]["period_misalignment"] == 10
    assert s["groups_without_regulatory_anchor"] == 1
    assert len(s["flagged"]) == 16
