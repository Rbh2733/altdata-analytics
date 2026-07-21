"""Scorecard: estimates vs truth, for scored quarters only.

This is the only layer that reads data/truth/. It consumes the
estimation layer's committed outputs (outputs/estimates.csv), joins them
to truth, and measures error; it never imports simulation internals.
"""

import numpy as np
import pandas as pd

import config

METHODS = ["m1", "m2", "m3", "m4"]
CI_KPIS = ("revenue", "actives")


def load_truth(root=None):
    root = config.ROOT if root is None else root
    return pd.read_csv(root / "data" / "truth" / "truth_kpis.csv")


def load_events(root=None):
    root = config.ROOT if root is None else root
    return pd.read_csv(root / "data" / "truth" / "planted_events.csv")


def build_cells(estimates: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    """One row per scored (method, company, quarter, kpi) with APE."""
    t = truth.melt(id_vars=["company", "quarter"],
                   value_vars=config.KPIS, var_name="kpi", value_name="truth")
    e = estimates[estimates["scored"] == 1].copy()
    cells = e.merge(t, on=["company", "quarter", "kpi"], how="left", validate="m:1")
    if cells["truth"].isna().any():
        raise ValueError("scored estimate cell with no matching truth row")
    with np.errstate(divide="ignore", invalid="ignore"):
        cells["ape"] = (cells["estimate"] - cells["truth"]).abs() / cells["truth"].abs()
    return cells


def mape_tables(cells: pd.DataFrame) -> dict:
    by_kpi = (cells.groupby(["method", "kpi"])["ape"]
              .agg(["mean", "median"]).reset_index())
    rev_by_q = (cells[cells["kpi"] == "revenue"]
                .groupby(["method", "quarter"])["ape"].mean().reset_index())
    agg_rev = (cells[cells["kpi"] == "revenue"]
               .groupby("method")["ape"].mean().to_dict())
    return {"by_kpi": by_kpi, "revenue_by_quarter": rev_by_q,
            "revenue_aggregate": agg_rev}


def coverage_table(estimates: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    """Fraction of scored revenue/actives cells whose interval contains
    truth, per method and KPI."""
    t = truth.melt(id_vars=["company", "quarter"],
                   value_vars=list(CI_KPIS), var_name="kpi", value_name="truth")
    e = estimates[(estimates["scored"] == 1)
                  & (estimates["kpi"].isin(CI_KPIS))].copy()
    e = e.merge(t, on=["company", "quarter", "kpi"], how="left", validate="m:1")
    e["covered"] = ((e["ci_lo"] <= e["truth"]) & (e["truth"] <= e["ci_hi"]))
    out = (e.groupby(["method", "kpi"])
           .agg(cells=("covered", "size"), covered=("covered", "sum"))
           .reset_index())
    out["coverage"] = out["covered"] / out["cells"]
    return out


def pathology_costs(cells: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Revenue MAPE per method in each pathology quarter: the uncorrected
    cost and what the corrections bought, stated per quarter."""
    rows = []
    rev = cells[cells["kpi"] == "revenue"]
    for _, ev in events.iterrows():
        q = ev["quarter"]
        row = {"pathology": ev["pathology"], "quarter": q}
        for m in METHODS:
            row[f"{m}_revenue_mape"] = float(
                rev[(rev["method"] == m) & (rev["quarter"] == q)]["ape"].mean())
        rows.append(row)
    return pd.DataFrame(rows)
