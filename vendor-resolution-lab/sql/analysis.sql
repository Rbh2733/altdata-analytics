-- Analytical layer over the resolved vendor spend, executed by DuckDB
-- (sql/run_sql.py). Views: resolved (pipeline output), labels (ground truth,
-- used here only for the accuracy-by-week cut).

-- 1. Top vendors by resolved spend, with share of total
SELECT
    final_vendor,
    category,
    COUNT(*) AS txns,
    ROUND(SUM(amount), 2) AS spend,
    ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 2) AS pct_of_total
FROM resolved
WHERE final_vendor <> ''
GROUP BY final_vendor, category
ORDER BY spend DESC
LIMIT 12;

-- 2. Category concentration: top-3 vendor share inside each category
WITH vendor_spend AS (
    SELECT category, final_vendor, SUM(amount) AS spend
    FROM resolved
    WHERE final_vendor <> ''
    GROUP BY category, final_vendor
), ranked AS (
    SELECT
        category, final_vendor, spend,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY spend DESC) AS rk,
        SUM(spend) OVER (PARTITION BY category) AS cat_spend
    FROM vendor_spend
)
SELECT
    category,
    ROUND(SUM(CASE WHEN rk <= 3 THEN spend ELSE 0 END) / MAX(cat_spend) * 100, 1)
        AS top3_share_pct,
    MAX(cat_spend)::DECIMAL(18, 2) AS category_spend
FROM ranked
GROUP BY category
ORDER BY category_spend DESC;

-- 3. Weekly resolution mix with week-over-week auto-match delta
WITH weekly AS (
    SELECT
        week,
        COUNT(*) AS rows_total,
        SUM(CASE WHEN method IN ('exact', 'fuzzy_auto') THEN 1 ELSE 0 END) AS auto_matched,
        SUM(CASE WHEN final_method = 'new_vendor_candidate' THEN 1 ELSE 0 END) AS new_vendor_rows
    FROM resolved
    GROUP BY week
)
SELECT
    week,
    rows_total,
    ROUND(100.0 * auto_matched / rows_total, 2) AS auto_match_pct,
    ROUND(100.0 * auto_matched / rows_total
          - LAG(100.0 * auto_matched / rows_total) OVER (ORDER BY week), 2)
        AS wow_delta_pp,
    new_vendor_rows
FROM weekly
ORDER BY week;

-- 4. New-vendor candidates: normalized cores first seen in the drift window,
--    ranked by spend at stake (the "should we add coverage" queue)
SELECT
    core,
    MIN(week) AS first_seen_week,
    COUNT(*) AS txns,
    ROUND(SUM(amount), 2) AS spend_at_stake
FROM resolved
WHERE final_method = 'new_vendor_candidate'
GROUP BY core
ORDER BY spend_at_stake DESC
LIMIT 15;

-- 5. Pipeline accuracy by week (joins ground truth, the check a synthetic
--    lab makes possible and a production panel approximates with audits)
SELECT
    r.week,
    COUNT(*) AS assigned_rows,
    ROUND(100.0 * SUM(CASE WHEN r.final_vendor = l.true_vendor THEN 1 ELSE 0 END)
          / COUNT(*), 2) AS precision_pct
FROM resolved r
JOIN labels l ON r.raw_id = l.raw_id
WHERE r.final_vendor <> ''
GROUP BY r.week
ORDER BY r.week;
