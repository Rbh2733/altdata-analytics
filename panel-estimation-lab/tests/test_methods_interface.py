"""All four methods share one interface and emit a complete grid."""

import inspect

import numpy as np

import config
from estimation import methods

METHOD_FNS = [methods.m1_naive, methods.m2_weighted,
              methods.m3_weighted_qa, methods.m4_calibrated]


def _panel_public(shop):
    panel = {"transactions": shop.panel_transactions(),
             "panelists": shop.panelists()}
    public = {"census_margins": shop.census_margins(),
              "companies": shop.companies(),
              "reported_before": shop.reported_before}
    return panel, public


def test_methods_share_signature():
    sigs = {tuple(inspect.signature(f).parameters) for f in METHOD_FNS}
    assert sigs == {("quarter", "panel", "public")}


def test_all_methods_emit_full_grid_no_nans(shop):
    panel, public = _panel_public(shop)
    for quarter in ("2022Q1", "2023Q2", "2024Q4"):
        for fn in METHOD_FNS:
            out = fn(quarter, panel, public)
            assert list(out.columns) == ["company", "kpi", "estimate"]
            assert len(out) == 6 * len(config.KPIS)
            assert out["estimate"].notna().all()
            assert np.isfinite(out["estimate"]).all()
            rev = out[out["kpi"] == "revenue"]["estimate"]
            assert (rev >= 0).all()
            # the corrected rungs never lose a company entirely; the naive
            # rungs legitimately hit zero on Bramblebox after the
            # descriptor change, which is the planted wreck
            if fn in (methods.m3_weighted_qa, methods.m4_calibrated):
                assert (rev > 0).all()
