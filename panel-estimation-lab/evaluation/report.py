"""Render the scorecard: scorecard.csv, scorecard.md, metrics.json."""

import json

import pandas as pd

import config
from evaluation import scorecard as sc


def _pct(x):
    return f"{100.0 * x:.1f}%"


def render(estimates: pd.DataFrame, bootstrap_b: int,
           root=None, out_dir=None) -> dict:
    root = config.ROOT if root is None else root
    out = (config.OUTPUT_DIR if out_dir is None else out_dir)
    out.mkdir(parents=True, exist_ok=True)

    truth = sc.load_truth(root)
    events = sc.load_events(root)
    cells = sc.build_cells(estimates, truth)
    tables = sc.mape_tables(cells)
    cov = sc.coverage_table(estimates, truth)
    costs = sc.pathology_costs(cells, events)

    csv = cells[["method", "company", "quarter", "kpi",
                 "estimate", "truth", "ape"]].sort_values(
        ["method", "company", "quarter", "kpi"]).reset_index(drop=True)
    csv_fmt = csv.copy()
    for col, fmt in (("estimate", ".4f"), ("truth", ".4f"), ("ape", ".6f")):
        csv_fmt[col] = csv_fmt[col].map(lambda v: format(v, fmt))
    csv_fmt.to_csv(out / "scorecard.csv", index=False, lineterminator="\n",
                   encoding="utf-8")

    # ---------------------------------------------------------- markdown
    L = ["# Backtest Scorecard", "",
         f"Scored quarters: {config.SCORED_QUARTERS[0]} through "
         f"{config.SCORED_QUARTERS[-1]} (the four 2022 quarters are warmup "
         "and feed calibration history only). 6 companies x 8 quarters per "
         "method and KPI. APE = |estimate - truth| / truth; MAPE averages "
         "APE over companies and quarters. Median APE runs alongside "
         "because MAPE is outlier-dominated by design here.", ""]

    L += ["## MAPE by method and KPI", ""]
    piv = tables["by_kpi"].pivot(index="kpi", columns="method", values="mean")
    med = tables["by_kpi"].pivot(index="kpi", columns="method", values="median")
    L.append("| kpi | " + " | ".join(f"{m} MAPE (median APE)" for m in sc.METHODS) + " |")
    L.append("|---|" + "---|" * len(sc.METHODS))
    for kpi in config.KPIS:
        row = [f"{_pct(piv.loc[kpi, m])} ({_pct(med.loc[kpi, m])})" for m in sc.METHODS]
        L.append(f"| {kpi} | " + " | ".join(row) + " |")
    L.append("")

    L += ["## Revenue MAPE by method and quarter", ""]
    rq = tables["revenue_by_quarter"].pivot(index="quarter", columns="method",
                                            values="ape")
    patho_q = dict(zip(events["quarter"], events["pathology"]))
    L.append("| quarter | " + " | ".join(sc.METHODS) + " | pathology |")
    L.append("|---|" + "---|" * (len(sc.METHODS) + 1))
    for q in config.SCORED_QUARTERS:
        row = [_pct(rq.loc[q, m]) for m in sc.METHODS]
        L.append(f"| {q} | " + " | ".join(row) + f" | {patho_q.get(q, '')} |")
    L.append("")

    L += ["## Pathology quarters: revenue MAPE, uncorrected vs corrected", "",
          "| pathology | quarter | m1 | m2 | m3 | m4 |", "|---|---|---|---|---|---|"]
    for _, r in costs.iterrows():
        L.append(f"| {r['pathology']} | {r['quarter']} | "
                 + " | ".join(_pct(r[f"{m}_revenue_mape"]) for m in sc.METHODS)
                 + " |")
    L.append("")

    L += [f"## {int(config.CI_LEVEL * 100)}% interval coverage "
          "(bootstrap, panelist resampling, B="
          f"{bootstrap_b})", "",
          "| method | kpi | covered / cells | coverage |", "|---|---|---|---|"]
    for _, r in cov.sort_values(["method", "kpi"]).iterrows():
        L.append(f"| {r['method']} | {r['kpi']} | {int(r['covered'])}/"
                 f"{int(r['cells'])} | {_pct(r['coverage'])} |")
    L.append("")
    (out / "scorecard.md").write_text("\n".join(L), encoding="utf-8", newline="\n")

    # ------------------------------------------------------------- json
    metrics = {
        "bootstrap_replicates": bootstrap_b,
        "ci_level": config.CI_LEVEL,
        "revenue_mape": {m: round(tables["revenue_aggregate"][m], 6)
                         for m in sc.METHODS},
        "mape_by_kpi": {
            kpi: {m: round(float(piv.loc[kpi, m]), 6) for m in sc.METHODS}
            for kpi in config.KPIS},
        "median_ape_by_kpi": {
            kpi: {m: round(float(med.loc[kpi, m]), 6) for m in sc.METHODS}
            for kpi in config.KPIS},
        "coverage": {
            m: {k: round(float(cov[(cov["method"] == m) & (cov["kpi"] == k)]
                               ["coverage"].iloc[0]), 6)
                for k in sc.CI_KPIS} for m in sc.METHODS},
        "pathology_quarters": {
            r["pathology"]: {
                "quarter": r["quarter"],
                **{f"{m}_revenue_mape": round(r[f"{m}_revenue_mape"], 6)
                   for m in sc.METHODS}}
            for _, r in costs.iterrows()},
    }
    (out / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")

    cov_m4 = cov[(cov["method"] == "m4") & (cov["kpi"] == "revenue")].iloc[0]
    return {
        "revenue_mape": tables["revenue_aggregate"],
        "m4_revenue_covered": int(cov_m4["covered"]),
        "m4_revenue_cells": int(cov_m4["cells"]),
    }
