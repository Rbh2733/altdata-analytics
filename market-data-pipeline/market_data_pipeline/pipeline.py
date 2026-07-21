"""Pipeline orchestration: ingest, normalize, reconcile, persist, report.

The offline path (default) reads the committed fixtures, touches no
network, needs no keys, and produces byte-identical outputs on every run.
The live path fetches real data for real tickers: EDGAR always works
(keyless), while the vendor clients participate only when their API keys
are present, and are skipped with a printed notice otherwise.
"""

from pathlib import Path

from .clients import EdgarClient, FmpClient, PolygonClient
from .normalize import NORMALIZERS
from .reconcile import reconcile, summarize
from .report import (
    write_disagreement_report,
    write_metrics_json,
    write_resolved_csv,
)
from .sqlrunner import run_sql
from .store import build_store

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILES = [
    "resolved_fundamentals.csv",
    "disagreement_report.md",
    "metrics.json",
    "sql_report.md",
]


def make_clients(fixtures_dir=None):
    return [
        EdgarClient(fixtures_dir),
        FmpClient(fixtures_dir),
        PolygonClient(fixtures_dir),
    ]


def collect_observations(clients, tickers, live=False):
    """Fetch or load payloads per source per ticker; normalize to canonical."""
    observations = []
    for client in clients:
        if live and not client.available_live():
            print(f"    skipping {client.source_name}: no API key in environment")
            continue
        normalizer = NORMALIZERS[client.source_name]
        for ticker in tickers:
            if not live and not client.fixture_path(ticker).exists():
                continue
            payload = client.get_payload(ticker, live=live)
            observations.extend(normalizer(payload, ticker))
    return observations


def run(out_dir, live=False, tickers=None, fixtures_dir=None, echo_sql=True):
    """Full pipeline run. Returns the summary dict."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    clients = make_clients(fixtures_dir)

    if tickers is None:
        if live:
            raise ValueError("live mode requires --tickers")
        tickers = clients[0].fixture_tickers()
        if not tickers:
            raise FileNotFoundError("no committed fixtures found for edgar")

    mode = "live" if live else "offline (committed fixtures, no network)"
    print(f"[1/5] collecting payloads for {len(tickers)} tickers, mode: {mode}")
    observations = collect_observations(clients, tickers, live=live)
    print(f"      {len(observations)} canonical observations")

    print("[2/5] reconciling groups and measuring disagreement")
    reconciled = reconcile(observations)
    summary = summarize(reconciled, observations)
    flagged = summary["groups"] - summary["classification"]["agreement"]
    print(f"      {summary['groups']} groups, {flagged} flagged")

    print("[3/5] writing resolved fundamentals, disagreement report, metrics")
    write_resolved_csv(reconciled, out_dir / "resolved_fundamentals.csv")
    write_disagreement_report(reconciled, summary,
                              out_dir / "disagreement_report.md")
    write_metrics_json(summary, out_dir / "metrics.json")

    print("[4/5] building DuckDB store from schema.sql")
    db_path = build_store(out_dir / "market_data.duckdb", observations, reconciled)

    print("[5/5] running sql/analysis.sql over the store")
    run_sql(db_path, out_dir / "sql_report.md", echo=echo_sql)

    print(f"done. {out_dir.name}/: " + ", ".join(OUTPUT_FILES))
    return summary
