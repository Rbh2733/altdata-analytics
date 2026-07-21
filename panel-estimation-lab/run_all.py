"""End-to-end runner: python run_all.py (no arguments, no flags, offline).

Steps run as separate stages with an explicit data boundary: generation
writes data/, estimation reads only data/panel/ and data/public/ and
writes estimates plus the QA report, evaluation alone reads data/truth/
and scores the committed estimates. Returns code 1 if a QA hard check
fails or the scorecard cannot be rendered.
"""

import numpy as np
import pandas as pd

import config


def run_generation(root=None, verbose=True):
    from simulation import generate
    return generate.main(root=root, verbose=verbose)


def run_estimation(root=None, out_dir=None, verbose=True, b_reps=None):
    """The shop's whole day: QA, ladder, bootstrap. Touches only
    data/panel/ and data/public/ under root."""
    from estimation import loader, methods, uncertainty

    root = config.ROOT if root is None else root
    out = config.OUTPUT_DIR if out_dir is None else out_dir
    out.mkdir(parents=True, exist_ok=True)

    shop = loader.ShopData(root)
    reported = shop.reported_before(config.QUARTERS[-1])
    bundle, raw_engine, cor_engine = methods.build_engines(
        shop.panel_transactions(), shop.panelists(), shop.companies(),
        shop.census_margins(), reported)

    failed = [c for c in bundle["checks"] if not c[1]]
    n_findings = (len(bundle["duplicates"]["detail"])
                  + len(bundle["wave"]["findings"])
                  + len(bundle["outages"]["windows"])
                  + len(bundle["descriptor_changes"]["evidence"]))
    if verbose:
        print(f"[3/6] running panel QA ({n_findings} anomalies detected, "
              f"{len(bundle['checks']) - len(failed)} checks passed); "
              "writing outputs/qa_report.md")
    ones = np.ones(raw_engine.P)
    _, diags = cor_engine.raked_weights(ones)
    from estimation import qa as qa_mod
    qa_mod.write_qa_report(bundle, diags, out / "qa_report.md")
    if failed:
        for name, _, note in failed:
            print(f"      QA hard check FAILED: {name} ({note})")
        raise SystemExit(1)

    if verbose:
        print(f"[4/6] estimating {len(config.QUARTERS)} quarters x "
              f"{len(raw_engine.companies)} companies x 4 methods")
    grids = {
        "m1": raw_engine.m1(ones),
        "m2": raw_engine.m2(ones),
        "m3": cor_engine.m3(ones),
    }
    grids["m4"] = cor_engine.m4(ones, m3_est=grids["m3"])

    if verbose:
        b_label = config.BOOTSTRAP_B if b_reps is None else b_reps
        print(f"[5/6] bootstrapping intervals (B={b_label}, panelist "
              "resampling, seeded)")
    cis, B = uncertainty.bootstrap_cis(raw_engine, cor_engine, b_reps=b_reps)

    rows = []
    for m in ("m1", "m2", "m3", "m4"):
        for ci_i, co in enumerate(raw_engine.companies):
            for qi, q in enumerate(config.QUARTERS):
                for kpi in config.KPIS:
                    est = float(grids[m][kpi][ci_i, qi])
                    if kpi in ("revenue", "actives"):
                        lo = format(float(cis[m][kpi][0][ci_i, qi]), ".4f")
                        hi = format(float(cis[m][kpi][1][ci_i, qi]), ".4f")
                    else:
                        lo = hi = ""
                    rows.append({
                        "method": m, "company": co, "quarter": q, "kpi": kpi,
                        "estimate": format(est, ".4f"), "ci_lo": lo, "ci_hi": hi,
                        "scored": 1 if q in config.SCORED_QUARTERS else 0})
    est_df = pd.DataFrame(rows)
    est_df.to_csv(out / "estimates.csv", index=False, lineterminator="\n",
                  encoding="utf-8")
    return B


def run_evaluation(bootstrap_b, root=None, out_dir=None, verbose=True):
    """The judge: reads outputs/estimates.csv and data/truth/, writes the
    scorecard set."""
    from evaluation import report

    root = config.ROOT if root is None else root
    out = config.OUTPUT_DIR if out_dir is None else out_dir
    est = pd.read_csv(out / "estimates.csv")
    if verbose:
        print(f"[6/6] scoring {len(config.SCORED_QUARTERS)} quarters against "
              "truth (evaluation layer only)")
    summary = report.render(est, bootstrap_b, root=root, out_dir=out)
    if verbose:
        mape = summary["revenue_mape"]
        line = "  ".join(f"{m} {100 * mape[m]:.1f}%" for m in ("m1", "m2", "m3", "m4"))
        print(f"      revenue MAPE: {line}")
        print(f"      {int(config.CI_LEVEL * 100)}% interval coverage "
              f"(m4 revenue): {summary['m4_revenue_covered']}/"
              f"{summary['m4_revenue_cells']} cells")
    return summary


def main(root=None, out_dir=None, b_reps=None, verbose=True):
    if verbose:
        print(f"[1/6] simulating population and market ({config.N_POP} consumers, "
              "6 services, 12 quarters)")
        print("[2/6] sampling the biased panel; planted: duplicate feed day, "
              "recruitment wave, supplier outage, descriptor change")
    run_generation(root=root, verbose=verbose)
    B = run_estimation(root=root, out_dir=out_dir, verbose=verbose, b_reps=b_reps)
    run_evaluation(B, root=root, out_dir=out_dir, verbose=verbose)
    if verbose:
        print("done. rerun is byte-identical; run python sql/run_sql.py for "
              "the SQL layer.")


if __name__ == "__main__":
    main()
