"""Assembles the scorecard: scorecard.md, scorecard.csv, metrics.json.
The only place all five evaluation cuts come together."""

import json

import pandas as pd

import config
from evaluation import event_study, inflection_score, rank_quality, outcome_validation


def _fmt_pct(x):
    return "n/a" if pd.isna(x) else f"{100 * x:.1f}%"


def _fmt(x, nd=1):
    return "n/a" if pd.isna(x) else f"{x:.{nd}f}"


def render(scored_df: pd.DataFrame, level_bands: pd.DataFrame, truth: dict, out_dir):
    inflections = truth["inflections"]
    outcome_events = truth["outcome_events"]
    disclosed = truth["disclosed_revenues"]
    truth_fin = truth["truth_financials"]

    leadlag_raw = event_study.run(scored_df, inflections)
    leadlag_summary = event_study.summarize(leadlag_raw)

    prscore = inflection_score.score(scored_df, inflections)

    rank_raw = rank_quality.compute(scored_df, truth_fin)
    rank_summary = rank_quality.summarize(rank_raw)

    shutdown_v = outcome_validation.shutdown_validation(scored_df, outcome_events)
    funding_v = outcome_validation.funding_validation(scored_df, outcome_events)
    disc_summary, disc_detail = outcome_validation.disclosed_acquisition_validation(
        level_bands, disclosed, outcome_events)

    leadlag_raw.to_csv(out_dir / "leadlag.csv", index=False, lineterminator="\n")
    prscore.to_csv(out_dir / "scorecard.csv", index=False, lineterminator="\n")
    shutdown_v["detail"].to_csv(out_dir / "shutdown_detail.csv", index=False, lineterminator="\n")
    disc_detail.to_csv(out_dir / "disclosed_acquisition_detail.csv", index=False, lineterminator="\n")

    tier_gradient = rank_summary[rank_summary["cut"] == "tier"].set_index("key")["median_spearman"].to_dict()
    blended = rank_summary[(rank_summary["cut"] == "blended")]["median_spearman"]
    blended_val = float(blended.iloc[0]) if len(blended) else float("nan")

    metrics = {
        "n_vendors": int(scored_df["vendor_id"].nunique()),
        "n_scored_quarters": len(config.SCORED_QUARTERS),
        "tier_mix": scored_df.drop_duplicates(["vendor_id", "quarter"])["tier"].value_counts().to_dict(),
        "rank_quality_by_tier": {k: (None if pd.isna(v) else v) for k, v in tier_gradient.items()},
        "rank_quality_blended": None if pd.isna(blended_val) else blended_val,
        "leadlag_summary": leadlag_summary.to_dict(orient="records"),
        "inflection_precision_recall": prscore.to_dict(orient="records"),
        "shutdown_validation": {
            "n_shutdowns": shutdown_v["n_shutdowns"],
            "n_scored_at_t2": shutdown_v["n_scored_at_t2"],
            "bottom_quartile_share_at_t2": shutdown_v["bottom_quartile_share_at_t2"],
            "median_composite_at_t1": shutdown_v["median_composite_at_t1"],
            "population_median_composite": shutdown_v["population_median_composite"],
            "n_above_50_at_t1": len(shutdown_v["above_50_at_t1"]),
            "above_50_at_t1": shutdown_v["above_50_at_t1"],
        },
        "funding_validation": funding_v,
        "disclosed_acquisition_validation": disc_summary,
    }

    with open(out_dir / "metrics.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
        fh.write("\n")

    lines = []
    lines.append("# Scorecard\n")
    lines.append(f"Vendors: {metrics['n_vendors']}. Scored quarters: {metrics['n_scored_quarters']} "
                 f"({config.SCORED_QUARTERS[0]} to {config.SCORED_QUARTERS[-1]}).\n")
    lines.append("## Rank quality (median Spearman across scored quarters, composite vs forward true growth)\n")
    lines.append("| tier | median spearman |")
    lines.append("|---|---|")
    for tier in ("A", "B", "C"):
        lines.append(f"| {tier} | {_fmt(tier_gradient.get(tier), 3)} |")
    lines.append(f"| blended (reference only) | {_fmt(blended_val, 3)} |\n")

    lines.append("## Lead-lag summary (source vs truth inflection)\n")
    lines.append("| source | type | n_events | n_present | n_detected | detection_rate | median_lead_vs_regime_change | median_lead_vs_revenue |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, r in leadlag_summary.iterrows():
        lines.append(f"| {r['source']} | {r['event_type']} | {r['n_events']} | {r['n_present']} | "
                     f"{r['n_detected']} | {_fmt_pct(r['detection_rate'])} | "
                     f"{_fmt(r['median_lead_vs_regime_change'])} | {_fmt(r['median_lead_vs_revenue_realization'])} |")
    lines.append("")

    lines.append("## Inflection precision/recall grid (k quarters, by type and tier)\n")
    lines.append("| k | type | tier | n_flags | n_events | precision | recall |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in prscore.iterrows():
        lines.append(f"| {r['k']} | {r['type']} | {r['tier']} | {r['n_flags']} | {r['n_events']} | "
                     f"{_fmt_pct(r['precision'])} | {_fmt_pct(r['recall'])} |")
    lines.append("")

    lines.append("## Outcome validation\n")
    lines.append(f"- Shutdowns: {shutdown_v['n_shutdowns']} total; among the "
                 f"{shutdown_v['n_scored_at_t2']} with a scored composite two quarters prior, "
                 f"{_fmt_pct(shutdown_v['bottom_quartile_share_at_t2'])} sat in the bottom "
                 f"population quartile. Median composite one quarter before shutdown: "
                 f"{_fmt(shutdown_v['median_composite_at_t1'])} vs population median "
                 f"{_fmt(shutdown_v['population_median_composite'])}. "
                 f"{len(shutdown_v['above_50_at_t1'])} shutdown vendor(s) scored above 50 one quarter prior.")
    for row in shutdown_v["above_50_at_t1"]:
        lines.append(f"  - {row['vendor_id']} (tier {row['tier']}): composite {row['composite_t1']:.1f} "
                     f"the quarter before shutting down in {row['shutdown_quarter']}.")
    lines.append(f"- Funding: {funding_v['n_scored']} of {funding_v['n_funding_events']} rounds scored; "
                 f"median composite one quarter before a raise: "
                 f"{_fmt(funding_v['median_composite_before_round'])} vs population median "
                 f"{_fmt(funding_v['population_median_composite'])}. Impurity by design: "
                 f"runway-pressure raises pull this toward the population median from below.")
    lines.append(f"- Disclosed acquisitions ({disc_summary['n']} priced): band hit rate "
                 f"{_fmt_pct(disc_summary['band_hit_rate'])}, within-one-band "
                 f"{_fmt_pct(disc_summary['within_one_band_share'])}, median abs log10 error "
                 f"{_fmt(disc_summary['median_abs_log10_error'], 3)}. This is deliberately the "
                 f"least flattering table: without a reported-actuals anchor, levels are bands.\n")

    with open(out_dir / "scorecard.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    return metrics
