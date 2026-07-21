"""End-to-end pipeline run: ingest, normalize, reconcile, store, report.

Usage:
    python run_all.py                          offline demo (fixtures, no keys,
                                               no network); writes outputs/
    python run_all.py --live --tickers AAPL MSFT
                                               live mode against real APIs;
                                               writes runs/<UTC stamp>/
    python run_all.py --out-dir DIR            override the output directory

Every run writes its full artifact set (resolved_fundamentals.csv,
disagreement_report.md, metrics.json, sql_report.md) to the output
directory by default; nothing is print-only. The offline default writes to
outputs/ on purpose: those are the committed artifacts, and regenerating
them in place is how the repository stays checkable. Live runs write to a
timestamped directory under runs/ so they never disturb the committed,
deterministic outputs.

Live mode: EDGAR needs no key (set SEC_USER_AGENT to a real contact
address); fmp and polygon join automatically when FMP_API_KEY or
POLYGON_API_KEY are present, and are skipped with a notice otherwise.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:  # optional; a plain environment works identically
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from market_data_pipeline.pipeline import run

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(
        description="Multi-source fundamentals with measured disagreement."
    )
    ap.add_argument("--live", action="store_true",
                    help="fetch from real APIs instead of committed fixtures")
    ap.add_argument("--tickers", nargs="*", default=None,
                    help="tickers for live mode (offline mode uses fixtures)")
    ap.add_argument("--out-dir", default=None,
                    help="output directory (default: outputs/ offline, "
                         "runs/<UTC stamp>/ live)")
    args = ap.parse_args()

    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
    elif args.live:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = ROOT / "runs" / stamp
    else:
        out_dir = ROOT / "outputs"

    run(out_dir, live=args.live, tickers=args.tickers)


if __name__ == "__main__":
    main()
