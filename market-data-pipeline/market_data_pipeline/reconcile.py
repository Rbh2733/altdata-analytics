"""Group, measure disagreement, classify, resolve.

Observations are grouped by (ticker, metric, period). For each group the
pipeline computes the spread (max minus min) and the relative disagreement
(spread over the absolute median, in percent), then classifies before it
resolves, because the classification is the product: a resolved number
without a disagreement label is exactly the silent source-picking this
pipeline exists to replace.

Classification, checked in precedence order:

1. single_source: nothing to reconcile; the report says so instead of
   presenting one voice as a consensus.
2. unit_scale_mismatch: the max/min ratio sits within tolerance of a power
   of ten (100x or more). Values this far apart are not a data dispute,
   they are a dropped scale factor, and averaging them would be nonsense.
3. period_misalignment: sources agree on the fiscal label but their window
   end dates differ by more than PERIOD_SPAN_FLAG_DAYS. The values are
   describing different windows, so their numeric spread is not comparable
   disagreement and is flagged rather than graded.
4. agreement / minor_divergence / material_divergence by relative
   disagreement thresholds.

Resolution applies the source-reliability hierarchy from models.py:
regulatory over commercial over derived, alphabetical within a tier. The
resolved value is the best source's value, never a blend; when no
regulatory source covers a group, the group is resolved from vendor data
and marked as lacking a regulatory anchor.
"""

import statistics
from datetime import date

from .models import (
    ReconciledGroup,
    TIER_LABELS,
    resolution_order,
    source_tier,
)

AGREEMENT_TOLERANCE_PCT = 0.5
MINOR_TOLERANCE_PCT = 2.0
PERIOD_SPAN_FLAG_DAYS = 20
SCALE_FACTORS = (100.0, 1_000.0, 10_000.0, 1_000_000.0)
SCALE_RATIO_REL_TOL = 0.05


def _parse_date(s: str) -> date:
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def group_observations(observations) -> dict:
    """(ticker, metric, period) -> {source: observation}.

    A source contributing two observations to one group would mean the
    normalizer failed to deduplicate; that is a bug, so it fails loudly.
    """
    groups = {}
    for obs in observations:
        key = (obs.ticker, obs.metric, obs.period)
        by_source = groups.setdefault(key, {})
        if obs.source in by_source:
            raise ValueError(
                f"duplicate observation from {obs.source} for {key}; "
                "normalizer should have deduplicated"
            )
        by_source[obs.source] = obs
    return groups


def spread_of(values) -> float:
    return max(values) - min(values)


def relative_disagreement_pct(values) -> float:
    """Spread over absolute median, in percent. 0.0 for single values."""
    if len(values) < 2:
        return 0.0
    med = abs(statistics.median(values))
    if med == 0:
        return 0.0
    return spread_of(values) / med * 100.0


def looks_like_scale_mismatch(values) -> float:
    """Return the matched power-of-ten factor, or 0.0 if none.

    Only meaningful when all values share a sign and none is zero; a scale
    error multiplies, it never flips sign.
    """
    if len(values) < 2:
        return 0.0
    if any(v == 0 for v in values):
        return 0.0
    if not (all(v > 0 for v in values) or all(v < 0 for v in values)):
        return 0.0
    magnitudes = [abs(v) for v in values]
    ratio = max(magnitudes) / min(magnitudes)
    for factor in SCALE_FACTORS:
        if abs(ratio - factor) / factor <= SCALE_RATIO_REL_TOL:
            return factor
    return 0.0


def period_span_days(period_ends) -> int:
    dates = [_parse_date(d) for d in period_ends]
    return (max(dates) - min(dates)).days


def classify(values, period_ends):
    """(classification, note_fragment) for a group's values and window ends."""
    if len(values) == 1:
        return "single_source", ""
    factor = looks_like_scale_mismatch(values)
    if factor:
        magnitudes = [abs(v) for v in values]
        ratio = max(magnitudes) / min(magnitudes)
        return (
            "unit_scale_mismatch",
            f"max/min ratio {ratio:,.1f}, consistent with a dropped "
            f"{int(factor):,}x scale factor",
        )
    span = period_span_days(period_ends)
    if span > PERIOD_SPAN_FLAG_DAYS:
        return (
            "period_misalignment",
            f"window end dates span {span} days across sources",
        )
    rel = relative_disagreement_pct(values)
    if rel <= AGREEMENT_TOLERANCE_PCT:
        return "agreement", ""
    if rel <= MINOR_TOLERANCE_PCT:
        return "minor_divergence", ""
    return "material_divergence", ""


def reconcile(observations) -> list:
    """Full reconciliation: list of ReconciledGroup, deterministically sorted."""
    groups = group_observations(observations)
    out = []
    for (ticker, metric, period) in sorted(groups):
        by_source = groups[(ticker, metric, period)]
        sources = sorted(by_source)
        values = [by_source[s].value for s in sources]
        period_ends = [by_source[s].period_end for s in sources]
        classification, note = classify(values, period_ends)

        order = resolution_order(sources)
        resolved_source = order[0]
        resolved_value = by_source[resolved_source].value
        tier = source_tier(resolved_source)

        if classification == "single_source":
            note = f"only {resolved_source} reports this metric for the period"
        elif classification in ("minor_divergence", "material_divergence"):
            outlier = max(
                (s for s in sources if s != resolved_source),
                key=lambda s: abs(by_source[s].value - resolved_value),
            )
            dev = abs(by_source[outlier].value - resolved_value)
            dev_pct = dev / abs(resolved_value) * 100.0 if resolved_value else 0.0
            note = f"{outlier} deviates {dev_pct:.2f}% from the resolved value"

        out.append(
            ReconciledGroup(
                ticker=ticker,
                metric=metric,
                period=period,
                n_sources=len(sources),
                values={s: by_source[s].value for s in sources},
                period_ends={s: by_source[s].period_end for s in sources},
                spread=spread_of(values),
                rel_disagreement_pct=relative_disagreement_pct(values),
                classification=classification,
                resolved_value=resolved_value,
                resolved_source=resolved_source,
                resolved_tier=TIER_LABELS[tier],
                regulatory_anchor=(tier == 0),
                note=note,
            )
        )
    return out


def summarize(reconciled, observations) -> dict:
    """Summary metrics for metrics.json. Insertion order is deliberate."""
    classes = [
        "agreement",
        "minor_divergence",
        "material_divergence",
        "unit_scale_mismatch",
        "period_misalignment",
        "single_source",
    ]
    class_counts = {c: 0 for c in classes}
    resolved_by_source = {}
    no_anchor = 0
    for g in reconciled:
        class_counts[g.classification] += 1
        resolved_by_source[g.resolved_source] = (
            resolved_by_source.get(g.resolved_source, 0) + 1
        )
        if not g.regulatory_anchor:
            no_anchor += 1
    n_groups = len(reconciled)
    flagged = [
        {
            "ticker": g.ticker,
            "metric": g.metric,
            "period": g.period,
            "classification": g.classification,
            "rel_disagreement_pct": round(g.rel_disagreement_pct, 4),
            "values": {s: g.values[s] for s in sorted(g.values)},
            "resolved_source": g.resolved_source,
            "note": g.note,
        }
        for g in reconciled
        if g.classification != "agreement"
    ]
    return {
        "companies": len({g.ticker for g in reconciled}),
        "periods": sorted({g.period for g in reconciled}),
        "sources": sorted({o.source for o in observations}),
        "observations": len(observations),
        "groups": n_groups,
        "classification": class_counts,
        "agreement_rate_pct": (
            round(class_counts["agreement"] / n_groups * 100.0, 2)
            if n_groups else 0.0
        ),
        "resolved_by_source": {
            s: resolved_by_source[s] for s in sorted(resolved_by_source)
        },
        "groups_without_regulatory_anchor": no_anchor,
        "flagged": flagged,
    }
