"""Unit normalization and period labeling rules."""

import pytest

from market_data_pipeline.normalize import (
    apply_declared_scale,
    canonical_unit,
    fiscal_year_label,
)


def test_declared_scale_conversions():
    assert apply_declared_scale(1_500.0, "USD") == (1_500.0, "USD")
    assert apply_declared_scale(1_500.0, "thousands of USD") == (1_500_000.0, "USD")
    assert apply_declared_scale(2.5, "millions of USD") == (2_500_000.0, "USD")


def test_per_share_units_collapse_to_one_spelling():
    assert canonical_unit("USD/shares") == "USD/share"
    assert canonical_unit("USD / shares") == "USD/share"
    assert canonical_unit("USD/share") == "USD/share"
    value, unit = apply_declared_scale(3.14, "USD / shares")
    assert (value, unit) == (3.14, "USD/share")


def test_unknown_units_fail_loudly():
    with pytest.raises(ValueError):
        apply_declared_scale(1.0, "furlongs of EUR")


def test_fiscal_year_label_december_end():
    assert fiscal_year_label("2025-12-31") == "FY2025"


def test_fiscal_year_label_january_end_uses_prior_year():
    # Retail convention: the year ending 2026-01-31 is fiscal 2025.
    assert fiscal_year_label("2026-01-31") == "FY2025"


def test_fiscal_year_label_midyear_end():
    assert fiscal_year_label("2025-06-30") == "FY2025"
    assert fiscal_year_label("2025-09-27") == "FY2025"
