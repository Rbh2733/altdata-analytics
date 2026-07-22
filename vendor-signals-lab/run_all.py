"""End-to-end runner: python run_all.py [--tagger claude] (offline by
default, no arguments needed). Three stages run separately with an
explicit data boundary: generation writes data/, estimation reads only
data/exhaust/ and data/public/ and writes the QA/health/level outputs,
evaluation alone reads data/truth/ and scores the committed estimates.
Returns a nonzero status on a QA hard-check failure or an unrenderable scorecard.
"""

import argparse
import json
import sys

import pandas as pd

import config


def run_generation(root=None, verbose=True, seed=None):
    from simulation import generate
    return generate.main(root=root, verbose=verbose, seed=seed)


def _write_qa_report(bot_raw, bot_final, storm_flags, dedupe_collapsed,
                      frag_bridge, frag_evidence, cliff_flags, out_path):
    lines = ["# QA report\n"]
    lines.append("Shop-side only: every rule below is computed from "
                 "data/exhaust/ and data/public/, never from data/truth/.\n")

    lines.append("## P1: bot-traffic spike (z > 4 on the monthly log-return, "
                 "trailing 6 months, no corroborating jobs/spend move)\n")
    lines.append(f"- Raw z>4 candidates across the population: {len(bot_raw)}")
    lines.append(f"- Surviving after the no-corroboration filter: {len(bot_final)}")
    if not bot_final.empty:
        for _, r in bot_final.sort_values("z", ascending=False).head(10).iterrows():
            lines.append(f"  - {r['vendor_id']} {r['month']}: z={r['z']:.2f}")
    lines.append("")

    lines.append("## P2: job repost storm (unique fingerprints / raw postings < 0.4)\n")
    lines.append(f"- Vendor-quarters flagged: {len(storm_flags)}")
    if not storm_flags.empty:
        for _, r in storm_flags.iterrows():
            lines.append(f"  - {r['vendor_id']} {r['quarter']}: raw={r['raw']}, "
                         f"unique={r['unique']}, ratio={r['ratio']:.3f}")
    lines.append(f"- Relist-collapse window also absorbed {dedupe_collapsed} legitimate "
                 "background re-lists elsewhere in the population (counted, not hidden).\n")

    lines.append("## P3: descriptor fragmentation (panelist overlap > 0.5, amount "
                 "ratio >= 0.6, cadence ratio in [0.8, 1.25], all three agree)\n")
    lines.append(f"- Bridges found: {len(frag_bridge)}")
    for e in frag_evidence:
        lines.append(f"  - {e['new_descriptor']!r} -> {e['vendor_id']}: "
                     f"overlap={e['panelist_overlap']:.3f}, "
                     f"amount_ratio={e['amount_ratio']:.3f}, "
                     f"cadence_ratio={e['cadence_ratio']:.3f}")
    lines.append("")

    lines.append("## P4: coverage cliff (segment covered-vendor count drops "
                 "> 50% vs trailing 4-quarter mean)\n")
    lines.append(f"- Segment-quarters flagged: {len(cliff_flags)}")
    if not cliff_flags.empty:
        for _, r in cliff_flags.iterrows():
            lines.append(f"  - {r['segment']} {r['quarter']}: n_covered={r['n_covered']}, "
                         f"trailing_mean={r['trailing_mean']:.1f}")
    lines.append("")

    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def _write_tagger_report(val_df, preds, out_path):
    val_df = val_df.copy()
    val_df["pred"] = preds
    acc = float((val_df["pred"] == val_df["true_function"]).mean())
    funcs = ["engineering", "sales", "support", "other"]
    conf = pd.crosstab(val_df["true_function"], val_df["pred"]).reindex(
        index=funcs, columns=funcs, fill_value=0)
    lines = ["# Tagger report (mock, default)\n", f"Accuracy on 150 hand-labeled titles: "
             f"{100 * acc:.1f}%\n", "## Confusion matrix (rows = true, cols = predicted)\n"]
    lines.append("| true \\ pred | " + " | ".join(funcs) + " |")
    lines.append("|---" * (len(funcs) + 1) + "|")
    for f in funcs:
        row = " | ".join(str(int(conf.loc[f, g])) for g in funcs)
        lines.append(f"| {f} | {row} |")
    lines.append("")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return acc


def run_estimation(root=None, out_dir=None, verbose=True, tagger="mock"):
    from estimation.loader import ShopData
    from estimation import qa, coverage, composite, inflection, levels, tagger_mock

    root = config.ROOT if root is None else root
    out = config.OUTPUT_DIR if out_dir is None else out_dir
    out.mkdir(parents=True, exist_ok=True)

    shop = ShopData(root)
    final_q = config.QUARTERS[-1]

    cm, merged, frag_evidence, bridge = coverage.build(shop, final_q)
    withpct = composite.add_percentiles(merged)
    withcomp = composite.build_composite(withpct)
    flagged = inflection.add_flags(withcomp)

    cm.to_csv(out / "coverage_matrix.csv", index=False, lineterminator="\n")
    health_cols = ["vendor_id", "quarter", "segment", "tier", "composite",
                   "accel_flag", "stall_flag", "jobs_pct", "web_pct", "spend_pct",
                   "jobs_present", "web_present", "spend_present"]
    flagged[health_cols].to_csv(out / "health_index.csv", index=False, lineterminator="\n")
    flagged[flagged["accel_flag"] | flagged["stall_flag"]][
        ["vendor_id", "quarter", "tier", "composite", "accel_flag", "stall_flag"]
    ].to_csv(out / "inflections_flagged.csv", index=False, lineterminator="\n")

    lb_input = flagged.rename(columns={"jobs_n_reqs": "jobs_new_postings",
                                        "spend_presence": "spend_status"})
    level_bands = levels.build_level_bands(lb_input)
    level_bands.to_csv(out / "level_bands.csv", index=False, lineterminator="\n")

    # ---- QA report (re-derive the four detections at full history for the report)
    av = shop.as_of(final_q)
    bot_raw = qa.bot_spike_flags(av.web)
    dm = shop.descriptor_map()
    frag_bridge, frag_evidence2 = qa.detect_descriptor_fragmentation(av.spend, dm)
    resolved = qa.resolve_spend(av.spend, dm, frag_bridge)
    bot_final = qa.detect_bot_spikes(av.web, av.jobs, resolved)
    storm_flags = qa.detect_repost_storm(av.jobs)
    deduped = qa.dedupe_jobs(av.jobs)
    dedupe_collapsed = deduped.attrs.get("collapsed_count", 0)
    cliff_flags = qa.detect_coverage_cliff(resolved, shop.vendor_directory())
    _write_qa_report(bot_raw, bot_final, storm_flags, dedupe_collapsed,
                      frag_bridge, frag_evidence2, cliff_flags, out / "qa_report.md")

    # Note: postings_tagged / traffic_clean / spend_resolved are not
    # committed as separate CSVs (they would roughly double data/exhaust's
    # size for row-level duplicates of information already in
    # coverage_matrix.csv and level_bands.csv). sql/run_sql.py rebuilds
    # them in memory from the same estimation-layer functions used above,
    # for the SQL layer's views only.

    # ---- tagger report
    val = shop.tagger_validation_set()
    if tagger == "claude":
        from estimation import tagger_claude
        preds = tagger_claude.tag_titles(val["title"])
    else:
        preds = tagger_mock.tag_titles(val["title"])
    tagger_acc = _write_tagger_report(val, preds, out / "tagger_report.md")

    # ---- naive vs QA comparison
    naive = composite.build_naive_variant(shop, final_q)
    naive_for_flags = naive[["vendor_id", "quarter", "composite_naive"]].rename(
        columns={"composite_naive": "composite"})
    naive_flagged = inflection.add_flags(naive_for_flags)
    naive_flagged = naive_flagged.rename(columns={
        "accel_flag": "naive_accel_flag", "stall_flag": "naive_stall_flag"})

    merge_keys = ["vendor_id", "quarter"]
    cmp = flagged[merge_keys + ["composite", "accel_flag", "stall_flag", "tier"]].merge(
        naive[merge_keys + ["composite_naive"]], on=merge_keys, how="inner").merge(
        naive_flagged[merge_keys + ["naive_accel_flag", "naive_stall_flag"]],
        on=merge_keys, how="inner")
    cmp.to_csv(out / "naive_vs_qa.csv", index=False, lineterminator="\n")

    n_findings = len(bot_final) + len(storm_flags) + len(frag_bridge) + len(cliff_flags)
    if verbose:
        tier_counts = cm.drop_duplicates(["vendor_id", "quarter"])["tier"].value_counts()
        print(f"[4/7] shop QA: {n_findings} anomalies detected; writing outputs/qa_report.md")
        print(f"[5/7] tagging posting titles ({tagger}; accuracy {100*tagger_acc:.1f}%, "
              "outputs/tagger_report.md); building features")
        print(f"[6/7] scoring {cm['vendor_id'].nunique()} x "
              f"{cm['quarter'].nunique()} vendor-quarters: "
              f"tiers A={tier_counts.get('A',0)} B={tier_counts.get('B',0)} "
              f"C={tier_counts.get('C',0)}")
    return flagged, level_bands


def run_evaluation(scored_df, level_bands, root=None, out_dir=None, verbose=True):
    from evaluation import report as report_mod

    root = config.ROOT if root is None else root
    out = config.OUTPUT_DIR if out_dir is None else out_dir

    truth = {
        "inflections": pd.read_csv(root / "data" / "truth" / "inflections.csv"),
        "outcome_events": pd.read_csv(root / "data" / "truth" / "outcome_events.csv"),
        "disclosed_revenues": pd.read_csv(root / "data" / "truth" / "disclosed_revenues.csv"),
        "truth_financials": pd.read_csv(root / "data" / "truth" / "truth_financials.csv"),
    }
    if verbose:
        print("[7/7] judge: lead-lag, inflection P/R by tier, rank quality, outcome "
              "validation (evaluation layer is the sole reader of data/truth/)")
    metrics = report_mod.render(scored_df, level_bands, truth, out)
    return metrics


def main(root=None, out_dir=None, tagger="mock", verbose=True, seed=None):
    root = config.ROOT if root is None else root
    if verbose:
        print(f"[1/7] simulating {config.N_VENDORS} vendors across "
              f"{len(config.SEGMENTS)} segments, {config.N_QUARTERS} quarters of latent health")
        print("[2/7] generating outcome events (funding rounds, shutdowns, acquisitions)")
    gen_summary = run_generation(root=root, verbose=False, seed=seed)
    if verbose:
        print(f"[3/7] emitting exhaust: {gen_summary['n_postings']:,} job postings, "
              f"{gen_summary['n_web_rows']:,} traffic months, "
              f"{gen_summary['n_spend_rows']:,} spend rows; planted: bot spike, "
              "repost storm, descriptor fragmentation, coverage cliff")
    scored_df, level_bands = run_estimation(root=root, out_dir=out_dir, verbose=verbose, tagger=tagger)
    metrics = run_evaluation(scored_df, level_bands, root=root, out_dir=out_dir, verbose=verbose)
    if verbose:
        print("done. rerun is byte-identical; python sql/run_sql.py for SQL; "
              "pytest for the fences.")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tagger", choices=["mock", "claude"], default="mock")
    args = parser.parse_args()
    try:
        main(tagger=args.tagger)
    except SystemExit:
        raise
    except Exception as e:
        print(f"run_all failed: {e}", file=sys.stderr)
        raise SystemExit(1)
