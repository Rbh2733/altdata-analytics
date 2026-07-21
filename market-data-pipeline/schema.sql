-- market-data-pipeline DuckDB schema.
-- The store is rebuilt from this file on every run; the tables are a pure
-- function of that run's inputs. Values are canonical USD (raw dollars)
-- except eps_diluted, which is USD per share.

CREATE TABLE observations (
    ticker      TEXT NOT NULL,      -- fictional demo tickers on the offline path
    source      TEXT NOT NULL,      -- edgar, fmp, polygon
    metric      TEXT NOT NULL,      -- canonical metric name
    period      TEXT NOT NULL,      -- fiscal label as the source reports it
    period_end  DATE NOT NULL,      -- window end date as the source reports it
    value       DOUBLE NOT NULL,    -- canonical units
    unit        TEXT NOT NULL,      -- USD or USD/share
    as_of       DATE NOT NULL       -- when the source published or filed it
);

CREATE TABLE reconciled (
    ticker                 TEXT NOT NULL,
    metric                 TEXT NOT NULL,
    period                 TEXT NOT NULL,
    n_sources              INTEGER NOT NULL,
    spread                 DOUBLE NOT NULL,   -- max minus min, canonical units
    rel_disagreement_pct   DOUBLE NOT NULL,   -- spread over abs(median), percent
    classification         TEXT NOT NULL,
    resolved_value         DOUBLE NOT NULL,
    resolved_source        TEXT NOT NULL,
    regulatory_anchor      BOOLEAN NOT NULL,  -- false: resolved from vendor data alone
    note                   TEXT
);

-- One row per company and period, canonical metrics as columns, populated
-- from hierarchy-resolved values. This is the table a downstream consumer
-- would read; the reconciled table is the audit trail behind it.
CREATE VIEW resolved_fundamentals AS
SELECT
    ticker,
    period,
    MAX(CASE WHEN metric = 'revenue' THEN resolved_value END) AS revenue,
    MAX(CASE WHEN metric = 'net_income' THEN resolved_value END) AS net_income,
    MAX(CASE WHEN metric = 'eps_diluted' THEN resolved_value END) AS eps_diluted,
    MAX(CASE WHEN metric = 'total_assets' THEN resolved_value END) AS total_assets,
    MAX(CASE WHEN metric = 'operating_cash_flow' THEN resolved_value END)
        AS operating_cash_flow
FROM reconciled
GROUP BY ticker, period;
