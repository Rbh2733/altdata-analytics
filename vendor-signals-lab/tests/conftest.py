"""Session-scoped fixture: builds the full pipeline once into a tmp
tree, so the ~55 tests across this suite do not each pay the ~1-minute
generation+estimation+evaluation cost."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import run_all  # noqa: E402


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    tmp_root = tmp_path_factory.mktemp("vsl_pipeline")
    out_dir = tmp_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = run_all.main(root=tmp_root, out_dir=out_dir, verbose=False)
    from sql import run_sql
    run_sql.run(root=tmp_root, out_path=out_dir / "sql_report.md")
    return {
        "root": tmp_root,
        "out": out_dir,
        "metrics": metrics,
        "health": pd.read_csv(out_dir / "health_index.csv"),
        "coverage": pd.read_csv(out_dir / "coverage_matrix.csv"),
        "level_bands": pd.read_csv(out_dir / "level_bands.csv"),
        "naive_vs_qa": pd.read_csv(out_dir / "naive_vs_qa.csv"),
        "scorecard": pd.read_csv(out_dir / "scorecard.csv"),
        "leadlag": pd.read_csv(out_dir / "leadlag.csv"),
        "truth_inflections": pd.read_csv(tmp_root / "data" / "truth" / "inflections.csv"),
        "truth_events": pd.read_csv(tmp_root / "data" / "truth" / "outcome_events.csv"),
        "truth_financials": pd.read_csv(tmp_root / "data" / "truth" / "truth_financials.csv"),
        "planted": pd.read_csv(tmp_root / "data" / "truth" / "planted_pathologies.csv"),
    }
