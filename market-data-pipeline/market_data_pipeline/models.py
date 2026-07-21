"""Canonical data model shared by every layer of the pipeline.

Each source client returns its payload in the vendor's native shape; the
normalizers in normalize.py convert those payloads into MetricObservation
records, and everything downstream (reconciliation, storage, SQL) speaks
only this model. The source-reliability hierarchy lives here too, so the
resolution rule is data, not scattered if-statements.
"""

from dataclasses import dataclass


# The metrics the pipeline reconciles. Values are canonical USD (raw dollars,
# never thousands or millions) except eps_diluted, which is USD per share.
CANONICAL_METRICS = [
    "revenue",
    "net_income",
    "eps_diluted",
    "total_assets",
    "operating_cash_flow",
]

# Reliability tiers, lowest number wins. Regulatory filings beat commercial
# vendors, commercial vendors beat derived estimates. Within a tier the
# tie-break is alphabetical by source name, which is arbitrary but stated,
# deterministic, and visible in the output rather than an accident of dict
# ordering. Tier 2 (derived) is reserved for computed estimates; no current
# client sits there, but the resolution rule already handles it.
SOURCE_TIERS = {
    "edgar": 0,
    "fmp": 1,
    "polygon": 1,
}
TIER_LABELS = {0: "regulatory", 1: "commercial", 2: "derived"}


def source_tier(source: str) -> int:
    """Tier for a source name; unknown sources rank below everything known."""
    return SOURCE_TIERS.get(source, 2)


def resolution_order(sources) -> list:
    """Sources sorted best-first: (tier, name). Deterministic by construction."""
    return sorted(sources, key=lambda s: (source_tier(s), s))


@dataclass(frozen=True)
class MetricObservation:
    """One metric value, for one company and period, as one source reports it.

    value is already in canonical units (USD, or USD/share for eps_diluted);
    the per-source normalizer applies any declared scale before building the
    observation. period is the source's own fiscal label (e.g. "FY2025"),
    period_end is the ISO date the source attaches to the window, and as_of
    is when the source published or filed the figure. Keeping period and
    period_end separate is what lets reconciliation catch sources that agree
    on the label but not on the window.
    """

    ticker: str
    source: str
    metric: str
    period: str
    period_end: str
    value: float
    unit: str
    as_of: str


@dataclass
class ReconciledGroup:
    """Reconciliation result for one (ticker, metric, period) group.

    values and period_ends are keyed by source name. spread is max minus min
    in canonical units; rel_disagreement_pct is spread over the absolute
    median, in percent. classification is one of: agreement,
    minor_divergence, material_divergence, unit_scale_mismatch,
    period_misalignment, single_source. resolved_* record which source the
    hierarchy picked and what it said; regulatory_anchor is False when no
    tier-0 source covered the group, so the resolved figure rests on vendor
    data alone.
    """

    ticker: str
    metric: str
    period: str
    n_sources: int
    values: dict
    period_ends: dict
    spread: float
    rel_disagreement_pct: float
    classification: str
    resolved_value: float
    resolved_source: str
    resolved_tier: str
    regulatory_anchor: bool
    note: str
