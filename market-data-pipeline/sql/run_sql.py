"""Standalone runner for the analytical SQL layer.

Usage:
    python sql/run_sql.py                 # against outputs/market_data.duckdb
    python sql/run_sql.py --out-dir DIR   # against DIR/market_data.duckdb

Run run_all.py first; it builds the store this reads.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from market_data_pipeline.sqlrunner import run_sql  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="outputs",
                    help="directory holding market_data.duckdb (default: outputs)")
    args = ap.parse_args()
    out_dir = (PROJECT_ROOT / args.out_dir).resolve() \
        if not Path(args.out_dir).is_absolute() else Path(args.out_dir)
    db_path = out_dir / "market_data.duckdb"
    if not db_path.exists():
        raise FileNotFoundError(
            f"{db_path.name} not found in {args.out_dir}; run run_all.py first"
        )
    run_sql(db_path, out_dir / "sql_report.md")
    print(f"\nwrote {args.out_dir}/sql_report.md")


if __name__ == "__main__":
    main()
