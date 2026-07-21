# dbt Streaming-Catalog Analytics

A dbt-core plus DuckDB project over a synthetic music-streaming catalog: staging, intermediate, and marts layers in a star schema, 60 automated tests (50 generic, 10 singular), documentation as code, and an optional Streamlit dashboard. Everything runs locally from a committed seed; there are no external services or credentials.

## The data (synthetic, deterministic, honest)

The seed is not real catalog data. `scripts/generate_seed.py` generates all 85,000 rows deterministically (fixed RNG seed, stable row order, fixed numeric formatting, Unix line endings), and every artist, album, track, and record label name is invented. The committed CSV is exactly what the generator produces; regenerate and diff to verify:

```
python scripts/generate_seed.py
git diff --stat streaming_analytics/seeds/streaming_tracks_raw.csv   # no changes
```

Catalog shape, produced by the generator and checkable in the built database: 85,000 tracks, 28,125 unique artists, 12 genres, 8 fictional labels, 12 countries, release dates 2015 through 2025. Genre sound profiles, label market-share weights, artist career windows, and a popularity-linked stream-count distribution are all seeded so the marts have realistic structure (tiers, market share, audio fingerprints) without any real-world data. Because the data is generated, distributional findings describe the generator's assumptions, not the music industry.

## Layout

```
dbt-streaming-analytics/
    README.md                  # this file
    requirements.txt
    dashboard.py               # optional Streamlit front end over the marts
    scripts/
        generate_seed.py       # deterministic seed generator
    streaming_analytics/       # the dbt project (see its README for model detail)
        dbt_project.yml
        profiles.yml           # committed DuckDB profile, relative db path
        models/                # staging -> intermediate -> marts
        seeds/streaming_tracks_raw.csv
        tests/                 # 10 singular tests
        validate_data.py       # analytical spot-check queries
```

## Run it

```
pip install -r requirements.txt
cd streaming_analytics
dbt build --profiles-dir .
```

`dbt build` seeds the CSV, builds 8 models, and runs all 60 tests against a local `streaming.duckdb` file (gitignored, rebuilt on demand). The committed `profiles.yml` uses a relative database path, so no per-machine profile setup is needed; the `--profiles-dir .` flag is the whole configuration story.

Optional extras, from the same directory state:

```
python validate_data.py                  # from streaming_analytics/: tabular spot-checks
cd .. && streamlit run dashboard.py      # from this directory: interactive dashboard
```

Docs as code: `dbt docs generate && dbt docs serve` (from `streaming_analytics/`, with `--profiles-dir .`) renders the model and column descriptions in the schema yml files as a browsable lineage site.

## What this demonstrates

- Layered dbt architecture: one staging view per source, intermediate aggregation views at artist, genre, and label grain, and mart tables (two dimensions, one fact, one pre-aggregated report).
- Dimensional modeling: MD5 surrogate keys, degenerate dimensions on the fact, pre-calculated tier segments for dashboard filtering.
- A testing strategy where generic schema tests (unique, not_null, accepted_values, relationships) handle shape and singular SQL tests handle business logic: cross-layer stream-total reconciliation, market shares summing to 100, valid career timelines, feature-range checks.
- Reproducibility discipline: the seed regenerates byte-identically, so the entire warehouse is a pure function of one script.

The inner project README (`streaming_analytics/README.md`) documents each layer, model, and singular test.

## Limitations, stated plainly

- DuckDB and dbt-core on one machine. The layering and testing patterns are what transfer; there is no orchestration, incremental logic, or warehouse deployment here.
- The data is synthetic. Tiers, market shares, and audio fingerprints are properties of the generator's parameters, chosen to be plausible, not measured from any real catalog.
- One seed, one source. There is no snapshot or slowly-changing-dimension handling because the input is a static file.

Descriptive analytics on fictional data; nothing here is investment advice or a real-world market measurement.
