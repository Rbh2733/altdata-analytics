# Market Data Pipeline

The same fundamental metric for the same company and period differs across
data sources: vendors mis-scale, restate late, map fiscal labels to
calendar years, and quietly skip fields. Most pipelines pick one source and
never find out. This one ingests the same metrics from several sources,
normalizes to a canonical model, measures and reports the disagreement, and
only then resolves each group through an explicit source-reliability
hierarchy: regulatory filings over commercial vendors over derived
estimates. The disagreement report is the product; the resolved table is
the byproduct. Every number in this README was produced by this code, and
the generated reports in `outputs/` ship with the project so the numbers
are checkable without running anything.

## Architecture

```
clients/           per-source fetch: EDGAR (companyfacts, rate-limited,
                   keyless), fmp and polygon (real HTTP, key-gated);
                   every client also loads committed fixtures
normalize.py       per-source payload -> canonical MetricObservation
                   (field mapping, declared-scale conversion, fiscal
                   labeling that keeps the window end date)
reconcile.py       group by (company, metric, period); spread and relative
                   disagreement; classify; resolve via the hierarchy
store.py + schema.sql   DuckDB store rebuilt from the schema every run
sql/analysis.sql   coverage, disagreement leaderboard, classification mix,
                   resolved fundamentals view, resolution provenance
run_all.py         one command, offline by default, auto-saves all artifacts
```

Classification runs before resolution, in precedence order:
`single_source`, `unit_scale_mismatch` (max/min ratio near a power of ten;
that is a dropped scale factor, not a data dispute), `period_misalignment`
(same fiscal label, window end dates more than 20 days apart; the values
describe different windows, so their spread is not graded as disagreement),
then `agreement` / `minor_divergence` / `material_divergence` by relative
disagreement (spread over absolute median; bands at 0.5% and 2%).

Resolution never blends. The best-tier source's value is taken as-is
(regulatory > commercial > derived, alphabetical within a tier, stated and
deterministic), and any group with no regulatory source is flagged as
resolved without a regulatory anchor rather than passed off as settled.

## Run it (offline, no keys, no network)

```
pip install -r requirements.txt
python run_all.py        # fixtures -> outputs/: resolved_fundamentals.csv,
                         # disagreement_report.md, metrics.json, sql_report.md
pytest                   # 37 tests, offline
```

The committed demo covers 10 fictional companies, 2 fiscal years, 5
metrics, 3 sources: 296 observations into 100 reconciliation groups. The
offline path is deterministic: no wall-clock timestamps, fixture as-of
dates only, byte-identical outputs on every run (a test asserts this, and
another asserts the committed `outputs/` match a fresh run exactly).

## What the run catches (measured, this run)

- **A dropped scale factor.** fmp delivers ONFD FY2025 revenue as
  2,847,300 against 2,847,300,000 from EDGAR and polygon: a max/min ratio
  of exactly 1,000. Averaging would produce nonsense; grading it as a 99.9%
  disagreement would bury it. It is classified `unit_scale_mismatch`,
  resolved to the EDGAR figure, and the note names the suspected 1,000x
  factor.
- **A stale pre-restatement value.** QNTB's FY2024 revenue was restated
  from 1,538,200,000 to 1,412,400,000 in the FY2025 10-K (the EDGAR
  normalizer keeps the latest-filed fact, so the restatement supersedes the
  original automatically). polygon carries the restated figure; fmp still
  carries 1,538,200,000, an 8.91% relative disagreement. The hierarchy
  resolves to the restated regulatory value and the report names fmp as the
  outlier.
- **Fiscal labels on different windows.** NMBW's fiscal year ends January
  31. fmp maps labels to calendar years, so for "FY2025" it reports a
  window ending 2025-12-31 (revenue 742,800,000) while EDGAR and polygon
  report the window ending 2026-01-31 (754,900,000). All ten NMBW groups
  are classified `period_misalignment`, including the FY2024 eps group
  where the values happen to agree to the cent: same label, different
  window, 0.00% spread. Grouping by label alone would have compared those
  windows silently, which is the quietest failure in the whole class.

Full detail on every flagged group, including the three collection-noise
divergences and the coverage holes, is in `outputs/disagreement_report.md`;
`outputs/metrics.json` carries the machine-readable tally (84 of 100 groups
in clean agreement, 16 flagged, 1 resolved without a regulatory anchor).

## The SQL layer

`sql/analysis.sql` runs six cuts via DuckDB (`python sql/run_sql.py`)
against the store `run_all.py` builds from `schema.sql`: coverage by
source, per-metric coverage gaps, the disagreement leaderboard, the
classification mix, the resolved-fundamentals view, and resolution
provenance (which source supplied each resolved value; 99 groups from
EDGAR, 1 from fmp where EDGAR had no mapped tag). Results are committed in
`outputs/sql_report.md`.

## Live mode

```
python run_all.py --live --tickers AAPL MSFT
```

EDGAR needs no key; set `SEC_USER_AGENT` to a real contact address (the
SEC's fair-access policy requires it; the client rate-limits itself under
the SEC's 10 requests/second cap). fmp and polygon join automatically when
`FMP_API_KEY` or `POLYGON_API_KEY` are set (see `.env.example`) and are
skipped with a printed notice otherwise. Live runs write to a timestamped
directory under `runs/` so the committed, deterministic `outputs/` are
never disturbed.

## Limitations, stated plainly

- Fixture realism has a ceiling. The payloads are shaped like each source's
  real responses and the planted failures are modeled on real feed
  behavior, but the difficulty is whatever the generator seeds. Treat the
  offline results as properties of this dataset.
- Vendor API shapes drift. The fmp client matches the v3 statement
  endpoints and the polygon client matches the vX financials endpoint as
  documented; both vendors version and evolve their responses, and polygon
  explicitly labels vX experimental.
- EDGAR tag mapping is partial. Real filers spread revenue across dozens of
  us-gaap tags; this pipeline maps two. The TSSL fixture exists to show
  what happens when the mapping misses: the group loses its regulatory
  anchor visibly instead of silently.
- The fiscal labeling convention (January-through-May year ends label to
  the prior year) is a heuristic and will not match every issuer's own
  naming.
- Single-machine scale, two fiscal years, five metrics. The design
  (canonical model, measured disagreement, explicit hierarchy) is what
  scales; the implementation is meant to be read in an afternoon.

This is descriptive research tooling for measuring data quality across
sources. It is not investment advice.
