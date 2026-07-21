"""Determinism: the committed data equals a fresh regeneration, the
committed outputs equal a fresh estimation-plus-evaluation run, and the
committed SQL report equals a fresh in-process rebuild. The second check
is the suite's crown jewel: it proves determinism, README-number
honesty, and the absence of wall-clock in one bite. The third exists
because the SQL report is rendered text, and rendering is exactly where
environment dependence (terminal width, locale) likes to hide."""

import importlib.util
from pathlib import Path

DATA_FILES = [
    "panel/panel_transactions.csv",
    "panel/panelists.csv",
    "public/census_margins.csv",
    "public/companies.csv",
    "public/reported_actuals.csv",
    "truth/truth_kpis.csv",
    "truth/planted_events.csv",
]

OUTPUT_FILES = [
    "estimates.csv",
    "qa_report.md",
    "scorecard.csv",
    "scorecard.md",
    "metrics.json",
]


def _same_bytes(a: Path, b: Path):
    assert a.exists(), f"missing committed file {a.name}"
    assert b.exists(), f"missing regenerated file {b.name}"
    assert a.read_bytes() == b.read_bytes(), f"{a.name} differs on regeneration"


def test_generator_reproduces_committed_data(root, regen_data_root):
    for rel in DATA_FILES:
        _same_bytes(root / "data" / rel, regen_data_root / "data" / rel)


def test_pipeline_reproduces_committed_outputs(root, regen_out_dir):
    for rel in OUTPUT_FILES:
        _same_bytes(root / "outputs" / rel, regen_out_dir / rel)


def test_sql_report_reproduces_committed(root):
    """sql/run_sql.py's report text, rebuilt in-process from committed
    data and outputs, is byte-identical to the committed sql_report.md
    (the file is written with newline="\\n", so bytes equal the text)."""
    spec = importlib.util.spec_from_file_location(
        "run_sql_under_test", root / "sql" / "run_sql.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    committed = (root / "outputs" / "sql_report.md").read_bytes()
    assert committed == mod.build_report().encode("utf-8"), \
        "sql_report.md differs on regeneration"
