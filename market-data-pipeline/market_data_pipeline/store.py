"""DuckDB persistence, schema-file driven.

The store is rebuilt from schema.sql on every run (delete, create, insert),
so the database is always a pure function of the run's observations and
reconciliation results. The database file itself is not committed; the SQL
layer's committed artifact is outputs/sql_report.md, produced by running
sql/analysis.sql against this store.
"""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"


def build_store(db_path, observations, reconciled, schema_path=SCHEMA_PATH):
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    try:
        con.execute(Path(schema_path).read_text(encoding="utf-8"))
        con.executemany(
            "INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (o.ticker, o.source, o.metric, o.period, o.period_end,
                 o.value, o.unit, o.as_of)
                for o in observations
            ],
        )
        con.executemany(
            "INSERT INTO reconciled VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (g.ticker, g.metric, g.period, g.n_sources, g.spread,
                 g.rel_disagreement_pct, g.classification, g.resolved_value,
                 g.resolved_source, g.regulatory_anchor, g.note)
                for g in reconciled
            ],
        )
    finally:
        con.close()
    return db_path
