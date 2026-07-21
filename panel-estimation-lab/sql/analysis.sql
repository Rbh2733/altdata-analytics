-- Analytical layer over the panel and the estimates, executed by DuckDB
-- (sql/run_sql.py). Views registered by the runner:
--   panel_txns  post-QA transactions (deduped, alias-resolved, company-mapped)
--   panelists   panel roster with demographics and join/leave months
--   weights_q   raked panelist weights per quarter (corrected engine)
--   estimates   outputs/estimates.csv (all methods, all quarters)
--   reported    public reported actuals (prior quarters, via the temporal gate)
-- Ground truth is NOT registered: this layer runs shop-side, and the fence
-- stays up even for analysis.

-- 1. Cohort retention: adoption-quarter cohorts, subscription services,
--    weighted retention by quarters since adoption (triangle for the two
--    largest subscription services)
WITH qidx AS (
    SELECT panelist_id, company, quarter,
           (CAST(substr(quarter, 1, 4) AS INT) - 2022) * 4
               + CAST(substr(quarter, 6, 1) AS INT) - 1 AS qi
    FROM panel_txns
    WHERE company IN ('Streambird', 'Aurelo')
    GROUP BY ALL
), cohorts AS (
    SELECT panelist_id, company, MIN(qi) AS cohort_qi
    FROM qidx
    GROUP BY panelist_id, company
    HAVING MIN(qi) >= 1               -- 2022Q1 starters are left-censored
), sized AS (
    SELECT c.company, c.cohort_qi, q.qi - c.cohort_qi AS quarters_since,
           SUM(w.weight) AS w_present
    FROM cohorts c
    JOIN qidx q USING (panelist_id, company)
    JOIN weights_q w
      ON w.panelist_id = c.panelist_id
     AND (CAST(substr(w.quarter, 1, 4) AS INT) - 2022) * 4
             + CAST(substr(w.quarter, 6, 1) AS INT) - 1 = c.cohort_qi
    WHERE q.qi >= c.cohort_qi
    GROUP BY c.company, c.cohort_qi, q.qi - c.cohort_qi
)
SELECT company,
       2022 + cohort_qi // 4 AS cohort_year,
       1 + cohort_qi % 4 AS cohort_q,
       MAX(CASE WHEN quarters_since = 0 THEN 100.0 END) AS q0,
       ROUND(100.0 * MAX(CASE WHEN quarters_since = 1 THEN w_present END)
             / MAX(CASE WHEN quarters_since = 0 THEN w_present END), 1) AS q1,
       ROUND(100.0 * MAX(CASE WHEN quarters_since = 2 THEN w_present END)
             / MAX(CASE WHEN quarters_since = 0 THEN w_present END), 1) AS q2,
       ROUND(100.0 * MAX(CASE WHEN quarters_since = 3 THEN w_present END)
             / MAX(CASE WHEN quarters_since = 0 THEN w_present END), 1) AS q3,
       ROUND(100.0 * MAX(CASE WHEN quarters_since = 4 THEN w_present END)
             / MAX(CASE WHEN quarters_since = 0 THEN w_present END), 1) AS q4
FROM sized
WHERE cohort_qi <= 7
GROUP BY company, cohort_qi
ORDER BY company, cohort_qi;

-- 2. Penetration by segment: weighted vs unweighted panel penetration,
--    age x income cells, latest quarter, for the two most demographically
--    skewed subscription services (the composition correction made visible)
WITH customers AS (
    SELECT DISTINCT company, panelist_id
    FROM panel_txns
    WHERE quarter = '2024Q4' AND company IN ('Bramblebox', 'Aurelo')
), base AS (
    -- active panel only (weight > 0), so the weighted vs unweighted gap
    -- isolates the composition correction rather than attrition
    SELECT p.panelist_id, p.age_band, p.income_band, w.weight
    FROM panelists p
    JOIN weights_q w
      ON w.panelist_id = p.panelist_id AND w.quarter = '2024Q4'
)
SELECT a.company,
       COALESCE(b.age_band, 'ALL') AS age_band,
       COALESCE(b.income_band, 'ALL') AS income_band,
       COUNT(*) FILTER (WHERE c.panelist_id IS NOT NULL) AS panel_customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE c.panelist_id IS NOT NULL)
             / COUNT(*), 2) AS unweighted_pct,
       ROUND(100.0 * SUM(CASE WHEN c.panelist_id IS NOT NULL
                              THEN b.weight ELSE 0 END)
             / NULLIF(SUM(b.weight), 0), 2) AS weighted_pct
FROM base b
CROSS JOIN (SELECT DISTINCT company FROM customers) a
LEFT JOIN customers c
  ON c.company = a.company AND c.panelist_id = b.panelist_id
GROUP BY GROUPING SETS ((a.company, b.age_band, b.income_band), (a.company))
ORDER BY a.company, age_band NULLS FIRST, income_band;

-- 3. Market concentration per quarter: HHI (sum of squared shares) and
--    combined share of the two largest, from calibrated (m4) revenue
WITH shares AS (
    SELECT quarter, company, estimate,
           100.0 * estimate / SUM(estimate) OVER (PARTITION BY quarter) AS share_pct,
           ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY estimate DESC) AS rk
    FROM estimates
    WHERE method = 'm4' AND kpi = 'revenue'
)
SELECT quarter,
       ROUND(SUM(share_pct * share_pct), 0) AS hhi,
       ROUND(SUM(share_pct) FILTER (WHERE rk <= 2), 1) AS biggest_two_share_pct,
       MAX(company) FILTER (WHERE rk = 1) AS largest_company
FROM shares
GROUP BY quarter
ORDER BY quarter;

-- 4. Competitive share shift: quarter-over-quarter market share deltas
--    (m4), the twelve largest single-quarter movements
WITH s AS (
    SELECT company, quarter, estimate AS share_pct,
           estimate - LAG(estimate) OVER (PARTITION BY company ORDER BY quarter)
               AS delta_pp
    FROM estimates
    WHERE method = 'm4' AND kpi = 'market_share'
)
SELECT company, quarter, ROUND(share_pct, 2) AS share_pct,
       ROUND(delta_pp, 2) AS delta_pp
FROM s
WHERE delta_pp IS NOT NULL AND quarter >= '2023Q1'
ORDER BY ABS(delta_pp) DESC, company, quarter
LIMIT 12;

-- 5. Estimate vs reported, prior quarters: m4 revenue against reported
--    actuals where reporting exists (public data only; the fence holds)
WITH joined AS (
    SELECT e.company, e.quarter, e.estimate, r.revenue AS reported_revenue,
           100.0 * (e.estimate - r.revenue) / r.revenue AS gap_pct
    FROM estimates e
    JOIN reported r
      ON r.company = e.company AND r.quarter = e.quarter
    WHERE e.method = 'm4' AND e.kpi = 'revenue'
)
SELECT company,
       COUNT(*) AS quarters_compared,
       ROUND(AVG(ABS(gap_pct)), 2) AS avg_abs_gap_pct,
       ROUND(MAX(ABS(gap_pct)), 2) AS max_abs_gap_pct,
       MAX(quarter) FILTER (WHERE ABS(gap_pct) = (
           SELECT MAX(ABS(gap_pct)) FROM joined j2 WHERE j2.company = joined.company
       )) AS worst_quarter
FROM joined
GROUP BY company
ORDER BY avg_abs_gap_pct DESC;
