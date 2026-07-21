# Vendor Resolution Lab

A small, end-to-end entity-resolution and AI-tagging pipeline for vendor spend data, built the way the problem actually arrives: raw card-feed merchant strings ("SQ *NOTIONLABS 0423", "PYUSD-FLUXGRID AI") that have to be matched to a canonical vendor table, validated, monitored for drift, and analyzed in SQL. Every number in this README was produced by this code, and the generated reports in `outputs/` ship with the project so the numbers are checkable without running anything.

## What this demonstrates

- **Entity resolution in stages.** Normalize, then exact alias matching (longest alias wins, so "TWILIO SENDGRID" resolves to SendGrid, not Twilio), then blocked fuzzy matching with an auto-accept threshold and a review band, then an AI tagger for the tail. Each stage's precision is measured separately so nothing hides in a blended average.
- **An AI-tagging layer with a validation harness.** The tagger classifies unmatched strings against the vendor table or flags them as new-vendor candidates. The harness scores it against ground truth, so swapping the model changes a number, not a belief. A live Claude adapter ships alongside a deterministic mock, and the merge path is defensive: a row the tagger fails to return is surfaced as `tagger_dropped`, never silently accepted, and a tagger abstention on a review-band row keeps the resolver's candidate under its own `review_unconfirmed` label rather than erasing it. Both guardrail buckets are empty in the published run, which is what they should be until something breaks.
- **QA and drift monitoring.** Expectations (key uniqueness, referential integrity against the vendor master, value sanity) plus a weekly coverage monitor. When a week degrades, the alert also reports the most common leading tokens among the strings that failed to auto-match, so an unknown processor format names itself from the data.
- **A SQL analysis layer.** DuckDB queries over the resolved output: spend concentration, category shares, weekly resolution mix with week-over-week deltas, and a new-vendor queue ranked by spend at stake.

## The data (synthetic, deterministic, honest)

Real spend feeds cannot be published, so the lab generates its own: 60,000 transactions across 8 weekly batches against a master of 88 real software, AI, cloud, and SaaS vendors, seeded (`SEED = 7`) so every run is identical. The mess is deliberate and labeled in the generator: processor prefixes, store numbers and city tails, truncation to card-network descriptor widths, glued tokens, and adjacent-character typos. Weeks 7 and 8 carry a two-part drift event, the way real feed breaks arrive: a new processor format (`PYUSD-`) the normalizer has never seen, applied to a quarter of all rows, plus six vendors deliberately missing from the master (1,189 rows). Ground-truth labels exist only because the data is synthetic. The pipeline never reads them; only the evaluator and the SQL layer's accuracy-by-week cut do.

## Measured results (deterministic mock tagger, this run)

| Stage | Rows | Precision |
|---|---|---|
| Exact (normalized alias match) | 53,143 | 99.90% |
| Fuzzy auto-accept (score >= 0.90) | 69 | 100.00% |
| Tagger, review band (0.78 to 0.90) | 300 | 100.00% |
| Tagger, unmatched tail | 5,236 | 97.17% |

- Coverage: 97.9% of rows assigned a canonical vendor.
- New-vendor detection: 1,063 of 1,189 seeded novel-vendor rows flagged (89.4% recall), and 1,063 of 1,252 total flags are truly novel (84.9% precision). Both sides are reported because a candidate queue that is a quarter noise is a real cost, and hiding it behind a recall number is how that cost ships.
- The worst failure mode, a novel vendor forced onto a canonical name, happened 126 times (0.21% of rows), all of them in the loose tagger tail. It is counted, not hidden, because knowing the false-merge rate is the difference between a matcher you can ship and one you can only demo.
- The drift monitor flagged week 7 (auto-match 82.6% vs a 90.9% trailing mean) and week 8, and its attribution surfaced `PYUSD` as the dominant leading token among failed matches (339 rows in week 7) with no prior knowledge of the format. Full detail in `outputs/qa_report.md`.

The auto-accept band is deliberately conservative. Ambiguity routes to the review band and the tagger, where a wrong answer is cheap to catch, rather than into silent auto-matches, where it is not.

## The SQL layer

`sql/analysis.sql` runs five analytical cuts via DuckDB (`python sql/run_sql.py`), including window functions for share-of-total, per-category top-3 concentration, and week-over-week deltas. The week-7 event is visible as a -8.07pp weekly delta, and the new-vendor queue surfaces the seeded vendors ranked by spend at stake, including their glued and format-prefixed variants. Results are written to `outputs/sql_report.md` so the analysis is inspectable without running anything.

## The live LLM tagger

`src/tagger_claude.py` is a drop-in replacement for the mock behind the same interface: batches of raw strings against the vendor table via the Claude API (`claude-opus-4-8`) with a strict JSON schema, instructed not to force matches. Because a schema cannot enforce row coverage, the adapter verifies every batch covers every sent row exactly once and fails loudly on a mismatch instead of letting a dropped row corrupt the merge. The published numbers use the deterministic mock so they are checkable by anyone without an API key; run `python run_all.py --tagger claude` with `anthropic` installed and a key in the environment to score the live model against the same ground truth.

## Run it

```
pip install -r requirements.txt
python run_all.py          # generate, resolve, tag, evaluate, QA
python sql/run_sql.py      # analytical SQL over the output
```

Python 3.10+. The only required dependency is DuckDB; the pipeline itself is standard library. A clean copy of this directory reproduces every artifact byte-for-byte (the generator is seeded and `data/` regenerates on each run).

## Limitations, stated plainly

- Single-machine scale. The design (staged matching, blocking, review bands, drift monitoring) is what scales; this implementation is meant to be read in an afternoon, not deployed.
- Synthetic data. The failure modes are modeled on real card-feed behavior, but the difficulty is whatever the generator seeds. Treat the precision numbers as properties of this dataset, not claims about production data.
- The mock tagger is a keyword-and-similarity heuristic, present so the harness runs reproducibly without a key. Its numbers are a floor, not a ceiling, for what the live adapter does.
- New-vendor candidates are not clustered. "QUORUM DATA", "QUORUMDATA", and "PYUSD QUORUM DATA" appear as separate queue entries; collapsing them is the natural next stage and the current output makes the need visible.
