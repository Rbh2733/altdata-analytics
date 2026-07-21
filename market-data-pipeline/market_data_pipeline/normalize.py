"""Per-source payload to canonical MetricObservation records.

Each normalizer knows one source's native shape and nothing else. Three
jobs happen here and only here:

1. Field mapping. Vendor field names (netIncome, net_income_loss,
   NetIncomeLoss) map to the canonical metric names in models.py.
2. Unit normalization. Values arrive in canonical USD. Sources that declare
   a scale (thousands, millions) are converted through UNIT_SCALE; a source
   that delivers a mis-scaled value while declaring raw USD cannot be fixed
   here, which is precisely why reconciliation checks for power-of-ten
   ratios downstream.
3. Period labeling. Each observation keeps both the fiscal label (FY2025)
   and the exact window end date the source reported. Reconciliation groups
   on the label and then inspects the dates, because "same label, different
   window" is a real and quiet failure mode across vendors.

EDGAR notes: a companyfacts payload repeats the same period across multiple
filings (the original 10-K and any later 10-K that restates it). The
normalizer keeps the record with the latest filed date, so a restated figure
supersedes the original, matching how the filings themselves work. The
fiscal label is derived from the period end date, NOT from the fact's fy
field, because EDGAR sets fy to the fiscal year of the FILING that reported
the fact, which is wrong for restatements of prior years.
"""

from datetime import date

from .models import MetricObservation

# Declared-scale conversion. Applied when a source states its unit; the
# canonical unit after conversion is plain USD (or USD/share).
UNIT_SCALE = {
    "USD": 1.0,
    "USD/share": 1.0,
    "thousands of USD": 1_000.0,
    "millions of USD": 1_000_000.0,
}

# Duration facts must look like a fiscal year, not a quarter.
ANNUAL_WINDOW_DAYS = (300, 400)


def canonical_unit(unit: str) -> str:
    """Collapse per-share unit spellings; pass everything else through."""
    if unit in ("USD/shares", "USD / shares", "USD/share"):
        return "USD/share"
    return unit


def apply_declared_scale(value: float, unit: str):
    """Convert a declared-scale value to canonical units.

    Returns (canonical_value, canonical_unit). Raises on units the pipeline
    has no rule for, because guessing a scale is worse than stopping.
    """
    unit = canonical_unit(unit)
    if unit not in UNIT_SCALE:
        raise ValueError(f"no unit conversion rule for {unit!r}")
    return value * UNIT_SCALE[unit], ("USD/share" if unit == "USD/share" else "USD")


def fiscal_year_label(period_end: str) -> str:
    """Fiscal label from a window end date.

    Convention: a fiscal year ending June or later is labeled by that
    calendar year; one ending January through May is labeled by the prior
    year (the retail convention, where FY2025 ends in early 2026). This is
    a heuristic; companies with fiscal years ending February through May are
    labeled by the prior year, which will not match every issuer's own
    naming. The README lists this under limitations.
    """
    y, m, _ = period_end.split("-")
    year = int(y) if int(m) >= 6 else int(y) - 1
    return f"FY{year}"


def _window_days(start: str, end: str) -> int:
    y1, m1, d1 = (int(x) for x in start.split("-"))
    y2, m2, d2 = (int(x) for x in end.split("-"))
    return (date(y2, m2, d2) - date(y1, m1, d1)).days


# ---------------------------------------------------------------------------
# EDGAR
# ---------------------------------------------------------------------------

# us-gaap tag to canonical metric. Deliberately partial: real filers use
# dozens of revenue-adjacent tags, and mapping them all is a project of its
# own. When a company reports under a tag this map lacks, the metric is
# simply absent from EDGAR's observations and reconciliation records the
# missing regulatory anchor instead of pretending.
EDGAR_TAG_TO_METRIC = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "NetIncomeLoss": "net_income",
    "EarningsPerShareDiluted": "eps_diluted",
    "Assets": "total_assets",
    "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
}
# When two tags map to the same metric for the same period, lower index wins.
EDGAR_TAG_PRIORITY = {tag: i for i, tag in enumerate(EDGAR_TAG_TO_METRIC)}


def normalize_edgar(payload: dict, ticker: str) -> list:
    """Canonical observations from a companyfacts payload.

    Filters to annual facts from 10-K filings, deduplicates repeated periods
    by latest filed date (restatements supersede originals), and derives the
    fiscal label from the window end date.
    """
    best = {}  # (metric, period) -> (filed, neg_priority, observation)
    gaap = payload.get("facts", {}).get("us-gaap", {})
    for tag, spec in gaap.items():
        metric = EDGAR_TAG_TO_METRIC.get(tag)
        if metric is None:
            continue
        priority = EDGAR_TAG_PRIORITY[tag]
        for unit_name, facts in spec.get("units", {}).items():
            for fact in facts:
                if fact.get("form") != "10-K" or fact.get("fp") != "FY":
                    continue
                start = fact.get("start")
                end = fact.get("end")
                if start is not None:  # duration fact; must span a fiscal year
                    days = _window_days(start, end)
                    if not (ANNUAL_WINDOW_DAYS[0] <= days <= ANNUAL_WINDOW_DAYS[1]):
                        continue
                value, unit = apply_declared_scale(
                    float(fact["val"]), canonical_unit(unit_name)
                )
                obs = MetricObservation(
                    ticker=ticker.upper(),
                    source="edgar",
                    metric=metric,
                    period=fiscal_year_label(end),
                    period_end=end,
                    value=value,
                    unit=unit,
                    as_of=fact.get("filed", end),
                )
                key = (metric, obs.period)
                rank = (fact.get("filed", ""), -priority)
                if key not in best or rank > best[key][0]:
                    best[key] = (rank, obs)
    return sorted(
        (obs for _, obs in best.values()), key=lambda o: (o.metric, o.period)
    )


# ---------------------------------------------------------------------------
# FMP
# ---------------------------------------------------------------------------


def _fmp_rows(payload, statement, field_map, out):
    for row in payload.get(statement, []):
        if row.get("period") != "FY":
            continue
        period = f"FY{row.get('calendarYear')}"
        end = row.get("date")
        as_of = row.get("fillingDate") or end
        for field_name, metric in field_map.items():
            raw = row.get(field_name)
            if raw is None:
                continue
            unit = "USD/share" if metric == "eps_diluted" else "USD"
            out.append(
                MetricObservation(
                    ticker=payload.get("symbol", "").upper(),
                    source="fmp",
                    metric=metric,
                    period=period,
                    period_end=end,
                    value=float(raw),
                    unit=unit,
                    as_of=as_of,
                )
            )


def normalize_fmp(payload: dict, ticker: str) -> list:
    """Canonical observations from a bundled FMP statements payload.

    FMP reports raw reported-currency values; no scale conversion applies.
    calendarYear is FMP's own fiscal label, taken at face value here so that
    a vendor whose calendar mapping disagrees with the filing window shows
    up downstream instead of being silently repaired.
    """
    if not payload.get("symbol"):
        payload = dict(payload, symbol=ticker.upper())
    out = []
    _fmp_rows(payload, "income_statement", {
        "revenue": "revenue",
        "netIncome": "net_income",
        "epsdiluted": "eps_diluted",
    }, out)
    _fmp_rows(payload, "balance_sheet", {"totalAssets": "total_assets"}, out)
    _fmp_rows(payload, "cash_flow", {"operatingCashFlow": "operating_cash_flow"}, out)
    return sorted(out, key=lambda o: (o.metric, o.period))


# ---------------------------------------------------------------------------
# Polygon
# ---------------------------------------------------------------------------

POLYGON_PATHS = {
    ("income_statement", "revenues"): "revenue",
    ("income_statement", "net_income_loss"): "net_income",
    ("income_statement", "diluted_earnings_per_share"): "eps_diluted",
    ("balance_sheet", "assets"): "total_assets",
    ("cash_flow_statement", "net_cash_flow_from_operating_activities"):
        "operating_cash_flow",
}


def normalize_polygon(payload: dict, ticker: str) -> list:
    """Canonical observations from a polygon vX financials payload.

    Every line item carries its own unit string, which is converted through
    the declared-scale rules; polygon's fiscal_year field is its own label
    and is kept as reported.
    """
    out = []
    for result in payload.get("results", []):
        if result.get("timeframe") != "annual":
            continue
        period = f"FY{result.get('fiscal_year')}"
        end = result.get("end_date")
        as_of = result.get("filing_date") or end
        financials = result.get("financials", {})
        for (statement, item), metric in POLYGON_PATHS.items():
            node = financials.get(statement, {}).get(item)
            if node is None or node.get("value") is None:
                continue
            value, unit = apply_declared_scale(
                float(node["value"]), canonical_unit(node.get("unit", "USD"))
            )
            out.append(
                MetricObservation(
                    ticker=ticker.upper(),
                    source="polygon",
                    metric=metric,
                    period=period,
                    period_end=end,
                    value=value,
                    unit=unit,
                    as_of=as_of,
                )
            )
    return sorted(out, key=lambda o: (o.metric, o.period))


NORMALIZERS = {
    "edgar": normalize_edgar,
    "fmp": normalize_fmp,
    "polygon": normalize_polygon,
}
