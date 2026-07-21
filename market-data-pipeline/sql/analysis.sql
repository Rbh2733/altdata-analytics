-- Analytical layer over the pipeline store, executed by DuckDB
-- (sql/run_sql.py). Tables: observations (canonical per-source records),
-- reconciled (per-group disagreement and resolution), and the
-- resolved_fundamentals view defined in schema.sql.

-- 1. Coverage by source: how much of the grid each source actually fills
SELECT
    source,
    COUNT(DISTINCT ticker) AS companies,
    COUNT(DISTINCT metric) AS metrics,
    COUNT(*) AS observations
FROM observations
GROUP BY source
ORDER BY source;

-- 2. Coverage gaps by metric: observation counts per source, side by side.
--    A cell below the max is a vendor hole the reconciler had to work around.
SELECT
    metric,
    SUM(CASE WHEN source = 'edgar' THEN 1 ELSE 0 END) AS edgar,
    SUM(CASE WHEN source = 'fmp' THEN 1 ELSE 0 END) AS fmp,
    SUM(CASE WHEN source = 'polygon' THEN 1 ELSE 0 END) AS polygon
FROM observations
GROUP BY metric
ORDER BY metric;

-- 3. Disagreement leaderboard: every flagged group, worst first
SELECT
    ticker,
    metric,
    period,
    n_sources,
    classification,
    ROUND(rel_disagreement_pct, 2) AS rel_disagreement_pct,
    resolved_source
FROM reconciled
WHERE classification <> 'agreement'
ORDER BY rel_disagreement_pct DESC, ticker, metric, period
LIMIT 20;

-- 4. Classification mix: how the group population splits
SELECT
    classification,
    COUNT(*) AS groups,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_groups
FROM reconciled
GROUP BY classification
ORDER BY groups DESC, classification;

-- 5. Resolved fundamentals, latest fiscal year (USD millions except eps)
SELECT
    ticker,
    period,
    ROUND(revenue / 1e6, 1) AS revenue_m,
    ROUND(net_income / 1e6, 1) AS net_income_m,
    ROUND(eps_diluted, 2) AS eps_diluted,
    ROUND(total_assets / 1e6, 1) AS total_assets_m,
    ROUND(operating_cash_flow / 1e6, 1) AS ocf_m
FROM resolved_fundamentals
WHERE period = (SELECT MAX(period) FROM reconciled)
ORDER BY ticker;

-- 6. Resolution provenance: which source supplied the resolved value, and
--    how many groups lack a regulatory anchor entirely
SELECT
    resolved_source,
    COUNT(*) AS groups,
    SUM(CASE WHEN regulatory_anchor THEN 0 ELSE 1 END) AS without_regulatory_anchor
FROM reconciled
GROUP BY resolved_source
ORDER BY groups DESC, resolved_source;
