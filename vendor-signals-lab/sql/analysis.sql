-- Five analytical cuts over the shop's committed outputs. Shop-side
-- only: truth is never registered as a view here, matching (and
-- restating) panel-estimation-lab's stricter stance versus its own
-- sibling. Views registered by sql/run_sql.py: directory, coverage,
-- health, postings_tagged, traffic_clean, spend_resolved.
-- Each cut below is delimited by a "-- @cut: <name>" marker that
-- sql/run_sql.py parses; do not remove the markers.

-- @cut: coverage_tier_by_segment_quarter
-- Tier distribution by segment x quarter (pivot). The coverage-cliff
-- quarters (2025Q2, 2025Q3) should read as visibly anomalous in the
-- ai_applications row: a spike in C (and drop in A/B) versus neighboring
-- quarters, with tier_reason = 'coverage_cliff' driving it.
SELECT
    c.segment,
    c.quarter,
    COUNT(*) FILTER (WHERE c.tier = 'A') AS tier_a,
    COUNT(*) FILTER (WHERE c.tier = 'B') AS tier_b,
    COUNT(*) FILTER (WHERE c.tier = 'C') AS tier_c,
    COUNT(*) FILTER (WHERE c.tier_reason = 'coverage_cliff') AS coverage_cliff_rows
FROM coverage c
GROUP BY c.segment, c.quarter
ORDER BY c.segment, c.quarter;

-- @cut: composite_leaderboard_by_tier
-- Top and bottom 5 composites per tier for the final scored quarter,
-- with the per-source percentiles that built each score. A tier-C
-- extreme literally cannot appear here post-shrinkage (composite is
-- pulled halfway to 50), which the table makes visible by eye.
WITH final_q AS (
    SELECT MAX(quarter) AS q FROM health
),
ranked AS (
    SELECT
        h.vendor_id, d.name, d.segment, h.tier, h.composite,
        h.jobs_pct, h.web_pct, h.spend_pct,
        RANK() OVER (PARTITION BY h.tier ORDER BY h.composite DESC, h.vendor_id) AS rank_top,
        RANK() OVER (PARTITION BY h.tier ORDER BY h.composite ASC, h.vendor_id) AS rank_bottom
    FROM health h
    JOIN directory d USING (vendor_id)
    WHERE h.quarter = (SELECT q FROM final_q)
)
SELECT * FROM ranked WHERE rank_top <= 5 OR rank_bottom <= 5
ORDER BY tier, composite DESC, vendor_id;

-- @cut: leadlag_shop_observable
-- For every vendor whose composite carries an acceleration flag, the
-- first quarter (within a 4-quarter lookback of the flagged quarter)
-- each source's own percentile crossed the same +15 rule the flagger
-- uses. This demonstrates hiring-first ordering inside SQL, without
-- ever touching data/truth/.
WITH deltas AS (
    SELECT
        vendor_id, quarter,
        jobs_pct - AVG(jobs_pct) OVER w2 AS jobs_delta,
        web_pct - AVG(web_pct) OVER w2 AS web_delta,
        spend_pct - AVG(spend_pct) OVER w2 AS spend_delta
    FROM health
    WINDOW w2 AS (PARTITION BY vendor_id ORDER BY quarter
                  ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING)
),
flagged AS (
    SELECT vendor_id, quarter AS flag_quarter FROM health WHERE accel_flag
),
crossings AS (
    SELECT f.vendor_id, f.flag_quarter, d.quarter AS cross_quarter,
           d.jobs_delta, d.web_delta, d.spend_delta
    FROM flagged f
    JOIN deltas d ON d.vendor_id = f.vendor_id
        AND d.quarter BETWEEN
            (SELECT MIN(quarter) FROM health h2 WHERE h2.vendor_id = f.vendor_id)
            AND f.flag_quarter
)
-- The composite over-triggers (see the README's honest-failure section),
-- so this can produce many rows; capped at 40 here for a readable report,
-- full detail is in outputs/inflections_flagged.csv.
SELECT
    vendor_id, flag_quarter,
    MIN(CASE WHEN jobs_delta >= 15 THEN cross_quarter END) AS jobs_first_cross,
    MIN(CASE WHEN web_delta >= 15 THEN cross_quarter END) AS web_first_cross,
    MIN(CASE WHEN spend_delta >= 15 THEN cross_quarter END) AS spend_first_cross
FROM crossings
GROUP BY vendor_id, flag_quarter
ORDER BY vendor_id, flag_quarter
LIMIT 40;

-- @cut: anomaly_report
-- QA rule firings visible from the committed shop-side artifacts: (a)
-- postings volume by vendor-quarter (the repost-storm vendor sits far
-- above its neighbors even after collapse), (b) corrected traffic
-- months by month (the bot-spike month stands out), (c) spend row
-- counts by segment-month (the coverage-cliff months read as a
-- structural zero, not a gradual decline).
SELECT 'postings_by_vendor_quarter' AS cut, key1, key2, CAST(n AS VARCHAR) AS value
FROM (
    SELECT vendor_id AS key1, quarter AS key2, COUNT(*) AS n
    FROM postings_tagged GROUP BY vendor_id, quarter
    HAVING COUNT(*) >= 30
    ORDER BY n DESC, key1, key2 LIMIT 15
) t
UNION ALL
SELECT 'corrected_traffic_months' AS cut, vendor_id AS key1, month AS key2,
       CAST(estimated_visits AS VARCHAR) AS value
FROM traffic_clean WHERE corrected
UNION ALL
SELECT 'spend_rows_by_segment_month' AS cut, d.segment AS key1,
       SUBSTR(CAST(s.txn_date AS VARCHAR), 1, 7) AS key2, CAST(COUNT(*) AS VARCHAR) AS value
FROM spend_resolved s JOIN directory d USING (vendor_id)
GROUP BY d.segment, SUBSTR(CAST(s.txn_date AS VARCHAR), 1, 7)
ORDER BY cut, key2, key1;

-- @cut: segment_share_shift
-- Within-panel spend share by segment, QoQ, via LAG. The two
-- coverage-cliff quarters are footnoted in the report text as a
-- measurement artifact (the ai_applications segment's panel access, not
-- the segment's actual market movement).
WITH seg_q AS (
    SELECT d.segment, SUBSTR(CAST(s.txn_date AS VARCHAR), 1, 4) || 'Q' ||
           CAST((((CAST(SUBSTR(CAST(s.txn_date AS VARCHAR), 6, 2) AS INTEGER) - 1) // 3) + 1) AS VARCHAR) AS quarter,
           SUM(s.amount) AS seg_amount
    FROM spend_resolved s JOIN directory d USING (vendor_id)
    GROUP BY d.segment, quarter
),
totals AS (
    SELECT quarter, SUM(seg_amount) AS total_amount FROM seg_q GROUP BY quarter
),
shares AS (
    SELECT sq.segment, sq.quarter, sq.seg_amount,
           sq.seg_amount / t.total_amount AS share
    FROM seg_q sq JOIN totals t USING (quarter)
)
SELECT segment, quarter, seg_amount, share,
       share - LAG(share) OVER (PARTITION BY segment ORDER BY quarter) AS share_qoq_delta
FROM shares
ORDER BY segment, quarter;
