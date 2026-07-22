"""sql_report.md regenerates byte-identical from the same committed
outputs, and no truth path or registered view name touches data/truth/."""

from pathlib import Path

from sql import run_sql

ROOT = Path(__file__).resolve().parent.parent


def test_no_truth_view_or_path():
    for name, relpath in run_sql.VIEWS.items():
        assert "truth" not in name
        if relpath is not None:
            assert "truth" not in relpath
    text = (ROOT / "sql" / "run_sql.py").read_text(encoding="utf-8")
    assert "data/truth" not in text
    sql_text = (ROOT / "sql" / "analysis.sql").read_text(encoding="utf-8")
    # allow prose mentions in comments explaining the boundary, but no
    # FROM/JOIN against a truth-named relation
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        assert "truth" not in stripped.lower()


def test_sql_report_byte_identical_rerun(built, tmp_path):
    out1 = tmp_path / "r1.md"
    out2 = tmp_path / "r2.md"
    run_sql.run(root=built["root"], out_path=out1)
    run_sql.run(root=built["root"], out_path=out2)
    assert out1.read_bytes() == out2.read_bytes()
