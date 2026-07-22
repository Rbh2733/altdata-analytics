"""Post-freeze robustness: regenerates the whole world under a second
seed (config.ROBUSTNESS_SEED) and reruns the full pipeline in an
isolated temp directory, then checks the qualitative survival criteria
stated before this check was ever run: lead ordering jobs > web > spend
unchanged, the tier A > B > C rank-quality gradient unchanged, and all
four pathologies still caught. Magnitudes are expected to move, and the
movement is reported rather than hidden.

Two further checks reuse the frozen seed-11 committed outputs directly
(no world regeneration needed): a threshold-sensitivity strip on the
inflection flagger's delta (10/15/20 points, floor/ceiling held fixed at
the frozen 55/45 so only one dial moves at a time), and an equal-weights
composite variant (1/3 jobs, web, spend instead of the frozen 0.35 /
0.20 / 0.45) rescored against forward ARR growth the same way the
headline rank-quality table is. Both are genuinely post-freeze: nothing
here changes a frozen parameter, only reruns the scoring math for
disclosure.

Excluded from run_all.py's runtime budget; run it separately:
    python robustness_check.py
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import config
import run_all
from estimation import composite as composite_mod
from estimation import inflection as inflection_mod
from evaluation import inflection_score, rank_quality

THRESHOLD_DELTAS = (10.0, 15.0, 20.0)
THRESHOLD_FLOOR = 55.0    # held fixed across all three deltas, on purpose:
THRESHOLD_CEILING = 45.0  # see the "one dial at a time" note above
THRESHOLD_K = 2


def _leadlag_ordering(metrics):
    rows = metrics["leadlag_summary"]
    med = {}
    for r in rows:
        src = r["source"]
        v = r["median_lead_vs_revenue_realization"]
        if v is None:
            continue
        med.setdefault(src, []).append(v)
    avg = {k: sum(v) / len(v) for k, v in med.items() if v}
    order = sorted(avg, key=lambda k: -avg[k])
    return order, avg


def _tier_gradient(metrics):
    return metrics.get("rank_quality_by_tier", {})


def threshold_sensitivity(health_df: pd.DataFrame, inflections_df: pd.DataFrame):
    """Population-pooled precision/recall/n_flags at k=2 for delta in
    THRESHOLD_DELTAS, floor/ceiling held at the frozen 55/45. Reuses
    estimation.inflection.add_flags and evaluation.inflection_score's own
    greedy matcher, so this is the same matching code the headline
    inflection-precision table uses, not a reimplementation."""
    rows = []
    for delta in THRESHOLD_DELTAS:
        flagged = inflection_mod.add_flags(
            health_df[["vendor_id", "quarter", "composite"]],
            delta=delta, floor=THRESHOLD_FLOOR,
            stall_delta=-delta, ceiling=THRESHOLD_CEILING)
        flagged = flagged.merge(health_df[["vendor_id", "quarter", "tier"]],
                                 on=["vendor_id", "quarter"])
        flags_df, events_df = inflection_score.build_flags_and_events(flagged, inflections_df)
        matched_flag_idx, matched_event_idx = inflection_score._greedy_match(
            flags_df, events_df, THRESHOLD_K)
        n_flags = len(flags_df)
        n_events = len(events_df)
        precision = len(matched_flag_idx) / n_flags if n_flags else float("nan")
        recall = len(matched_event_idx) / n_events if n_events else float("nan")
        rows.append({"delta": delta, "floor": THRESHOLD_FLOOR, "ceiling": THRESHOLD_CEILING,
                     "k": THRESHOLD_K, "n_flags": n_flags, "n_events": n_events,
                     "precision": precision, "recall": recall})
    return pd.DataFrame(rows)


def equal_weight_composite_check(health_df: pd.DataFrame, truth_financials: pd.DataFrame):
    """Rebuilds the composite from health_index.csv's own jobs_pct /
    web_pct / spend_pct columns (percentiles are unaffected by source
    weighting, only the blend is) using 1/3, 1/3, 1/3 instead of the
    frozen 0.35/0.20/0.45, then rescores the tier rank-quality gradient
    with the same evaluation.rank_quality module the headline table
    uses."""
    original_weights = dict(composite_mod.SOURCE_WEIGHTS)
    composite_mod.SOURCE_WEIGHTS = {"jobs": 1.0 / 3, "web": 1.0 / 3, "spend": 1.0 / 3}
    try:
        df = health_df.copy()
        df["composite_raw"] = df.apply(composite_mod._weighted_composite, axis=1)
        df["composite"] = np.where(
            df["tier"] == "C",
            50.0 + composite_mod.TIER_C_SHRINKAGE * (df["composite_raw"] - 50.0),
            df["composite_raw"])
    finally:
        composite_mod.SOURCE_WEIGHTS = original_weights

    rank_raw = rank_quality.compute(df, truth_financials)
    rank_summary = rank_quality.summarize(rank_raw)
    tier_gradient = rank_summary[rank_summary["cut"] == "tier"].set_index("key")["median_spearman"].to_dict()
    return tier_gradient


def main():
    baseline_path = config.OUTPUT_DIR / "metrics.json"
    if not baseline_path.exists():
        raise SystemExit("outputs/metrics.json not found; run `python run_all.py` first")
    with open(baseline_path, encoding="utf-8") as fh:
        baseline = json.load(fh)

    with tempfile.TemporaryDirectory(prefix="vsl_robustness_") as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "outputs").mkdir(parents=True, exist_ok=True)
        print(f"regenerating world under seed {config.ROBUSTNESS_SEED} in {tmp_root} ...")
        second = run_all.main(root=tmp_root, out_dir=tmp_root / "outputs",
                               verbose=False, seed=config.ROBUSTNESS_SEED)
        qa_text = (tmp_root / "outputs" / "qa_report.md").read_text(encoding="utf-8")

    base_order, base_avg = _leadlag_ordering(baseline)
    second_order, second_avg = _leadlag_ordering(second)
    base_tier = _tier_gradient(baseline)
    second_tier = _tier_gradient(second)

    def tier_monotonic(t):
        a, b, c = t.get("A"), t.get("B"), t.get("C")
        return a is not None and b is not None and c is not None and a > b > c

    health_df = pd.read_csv(config.OUTPUT_DIR / "health_index.csv")
    inflections_df = pd.read_csv(config.TRUTH_DIR / "inflections.csv")
    truth_financials_df = pd.read_csv(config.TRUTH_DIR / "truth_financials.csv")
    threshold_df = threshold_sensitivity(health_df, inflections_df)
    equal_weight_tier = equal_weight_composite_check(health_df, truth_financials_df)

    lines = ["# Robustness check (seed 12 vs seed 11, plus two frozen-seed sensitivity checks)\n"]
    lines.append(f"Seed {config.SEED} (frozen, committed run) vs seed "
                 f"{config.ROBUSTNESS_SEED} (this check, isolated temp directory, "
                 "not committed).\n")

    lines.append("## Lead ordering (source, mean of median lead vs revenue realization)\n")
    lines.append(f"- seed {config.SEED}: {base_order} {base_avg}")
    lines.append(f"- seed {config.ROBUSTNESS_SEED}: {second_order} {second_avg}")
    lines.append(f"- ordering unchanged: {base_order == second_order}\n")

    lines.append("## Tier rank-quality gradient (median Spearman by tier)\n")
    lines.append(f"- seed {config.SEED}: {base_tier}")
    lines.append(f"- seed {config.ROBUSTNESS_SEED}: {second_tier}")
    lines.append(f"- both monotonic A>B>C: "
                 f"{tier_monotonic(base_tier)} / {tier_monotonic(second_tier)}\n")

    lines.append(f"## Pathologies still caught (seed {config.ROBUSTNESS_SEED} QA report excerpt)\n")
    lines.append("```")
    qa_lines = qa_text.splitlines()
    for i, l in enumerate(qa_lines):
        if l.startswith("## P"):
            lines.append(l)
        elif l.startswith(("- Raw", "- Surviving", "- Vendor-quarters flagged",
                           "- Bridges found", "- Segment-quarters flagged")):
            lines.append(l)
    lines.append("```\n")

    lines.append(f"## Threshold sensitivity (delta = 10/15/20 points, k={THRESHOLD_K}, "
                 f"floor/ceiling held fixed at {THRESHOLD_FLOOR:.0f}/{THRESHOLD_CEILING:.0f}, "
                 f"population-pooled across type and tier, seed {config.SEED} frozen outputs)\n")
    lines.append("| delta | n_flags | n_events | precision | recall |")
    lines.append("|---|---|---|---|---|")
    for _, r in threshold_df.iterrows():
        lines.append(f"| {r['delta']:.0f} | {int(r['n_flags'])} | {int(r['n_events'])} | "
                     f"{100 * r['precision']:.1f}% | {100 * r['recall']:.1f}% |")
    lines.append("")

    lines.append(f"## Equal-weights composite (1/3 jobs, web, spend vs the frozen "
                 f"{composite_mod.SOURCE_WEIGHTS['jobs']}/{composite_mod.SOURCE_WEIGHTS['web']}/"
                 f"{composite_mod.SOURCE_WEIGHTS['spend']}, seed {config.SEED} frozen outputs)\n")
    lines.append(f"- frozen weights tier gradient: {base_tier}")
    lines.append(f"- equal weights tier gradient: {equal_weight_tier}\n")

    out_path = config.OUTPUT_DIR / "robustness_seed_check.md"
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
