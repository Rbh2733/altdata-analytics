"""Per-client fixture loading and payload parsing against committed fixtures."""

import pytest

from market_data_pipeline.clients import EdgarClient, FmpClient, PolygonClient
from market_data_pipeline.clients.base import MissingCredentialError
from market_data_pipeline.normalize import (
    normalize_edgar,
    normalize_fmp,
    normalize_polygon,
)


def test_fixture_tickers_align_across_sources():
    edgar, fmp, polygon = EdgarClient(), FmpClient(), PolygonClient()
    tickers = edgar.fixture_tickers()
    assert len(tickers) == 10
    assert fmp.fixture_tickers() == tickers
    assert polygon.fixture_tickers() == tickers


def test_edgar_fixture_parses_to_canonical():
    client = EdgarClient()
    obs = normalize_edgar(client.load_fixture("VLTX"), "VLTX")
    # 5 metrics x 2 fiscal years; the seeded 10-Q fact must be filtered out.
    assert len(obs) == 10
    assert all(o.source == "edgar" for o in obs)
    assert not any(o.period_end == "2025-09-30" for o in obs)
    rev = {o.period: o.value for o in obs if o.metric == "revenue"}
    assert rev["FY2025"] == 1_920_400_000


def test_edgar_restatement_supersedes_original():
    # QNTB FY2024 revenue appears twice in the companyfacts payload: the
    # original 10-K figure and the restated comparative from the FY2025 10-K.
    # The later filed date must win.
    client = EdgarClient()
    obs = normalize_edgar(client.load_fixture("QNTB"), "QNTB")
    rev24 = [o for o in obs if o.metric == "revenue" and o.period == "FY2024"]
    assert len(rev24) == 1
    assert rev24[0].value == 1_412_400_000
    assert rev24[0].as_of.startswith("2026")


def test_edgar_alternate_revenue_tag_is_mapped():
    # ARBL files revenue under RevenueFromContractWithCustomerExcludingAssessedTax.
    client = EdgarClient()
    obs = normalize_edgar(client.load_fixture("ARBL"), "ARBL")
    rev = [o for o in obs if o.metric == "revenue"]
    assert {o.period for o in rev} == {"FY2024", "FY2025"}


def test_fmp_fixture_parses_to_canonical():
    client = FmpClient()
    obs = normalize_fmp(client.load_fixture("VLTX"), "VLTX")
    assert len(obs) == 10
    assert all(o.source == "fmp" for o in obs)
    eps = {o.period: o.value for o in obs if o.metric == "eps_diluted"}
    assert eps["FY2025"] == pytest.approx(2.30)


def test_fmp_null_fields_are_skipped():
    client = FmpClient()
    obs = normalize_fmp(client.load_fixture("HLGR"), "HLGR")
    eps = [o for o in obs if o.metric == "eps_diluted"]
    assert {o.period for o in eps} == {"FY2024"}


def test_polygon_fixture_parses_to_canonical():
    client = PolygonClient()
    obs = normalize_polygon(client.load_fixture("VLTX"), "VLTX")
    assert len(obs) == 10
    assert all(o.source == "polygon" for o in obs)
    assert all(o.unit in ("USD", "USD/share") for o in obs)


def test_polygon_missing_statement_section_is_skipped():
    client = PolygonClient()
    obs = normalize_polygon(client.load_fixture("CNDP"), "CNDP")
    ocf = [o for o in obs if o.metric == "operating_cash_flow"]
    assert {o.period for o in ocf} == {"FY2024"}


def test_vendor_clients_refuse_live_mode_without_keys(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    fmp, polygon = FmpClient(), PolygonClient()
    assert not fmp.available_live()
    assert not polygon.available_live()
    with pytest.raises(MissingCredentialError):
        fmp.fetch("VLTX")
    with pytest.raises(MissingCredentialError):
        polygon.fetch("VLTX")


def test_edgar_client_is_keyless_and_rate_limited():
    client = EdgarClient()
    assert client.available_live()
    assert "User-Agent" in client.session.headers
    # The limiter enforces a minimum interval; two immediate calls must not
    # both pass without a wait being possible (interval is positive).
    from market_data_pipeline.clients.edgar import MIN_REQUEST_INTERVAL
    assert MIN_REQUEST_INTERVAL > 0.1  # under the SEC's 10 req/s cap
