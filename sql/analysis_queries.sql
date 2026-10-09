-- Euro Area Markets - analysis queries (SQLite: data/euro_markets.db)
-- Run:  sqlite3 data/euro_markets.db < sql/analysis_queries.sql

-- 1. Latest reading of every series with its month-on-month move
SELECT s.category, s.series_name, k.value, k.mom_change, s.unit, d.year_month AS as_of
FROM kpi_latest k
JOIN dim_series s USING (series_id)
JOIN dim_date   d USING (date_key)
ORDER BY s.category, s.series_name;

-- 2. ECB hiking & cutting cycle: every month the deposit rate changed
SELECT d.year_month, f.value AS dfr, f.mom_change AS change_pp,
       CASE WHEN f.mom_change > 0 THEN 'HIKE' ELSE 'CUT' END AS move
FROM fact_market_monthly f
JOIN dim_date d USING (date_key)
WHERE f.series_id = 'dfr' AND f.mom_change <> 0
ORDER BY d.year_month;

-- 3. Peak BTP-Bund spread per year (Italian sovereign risk)
WITH ranked AS (
    SELECT d.year, d.year_month, f.value,
           ROW_NUMBER() OVER (PARTITION BY d.year ORDER BY f.value DESC) AS rn
    FROM fact_market_monthly f
    JOIN dim_date d USING (date_key)
    WHERE f.series_id = 'spread_btp_bund'
)
SELECT year, year_month AS peak_month, ROUND(value, 0) AS peak_spread_bps
FROM ranked WHERE rn = 1
ORDER BY year;

-- 4. Months with an inverted AAA yield curve (2s10s < 0)
SELECT d.year, COUNT(*) AS inverted_months, ROUND(MIN(f.value), 0) AS deepest_bps
FROM fact_market_monthly f
JOIN dim_date d USING (date_key)
WHERE f.series_id = 'spread_2s10s' AND f.value < 0
GROUP BY d.year
ORDER BY d.year;

-- 5. EURO STOXX 50: annual return and 3-month rolling average level
SELECT d.year,
       ROUND(100.0 * (MAX(CASE WHEN d.month_num = 12 THEN f.value END)
                    / MAX(CASE WHEN d.month_num = 1 THEN f.value END) - 1), 1) AS jan_to_dec_pct
FROM fact_market_monthly f
JOIN dim_date d USING (date_key)
WHERE f.series_id = 'sx5e'
GROUP BY d.year
ORDER BY d.year;

SELECT d.year_month, f.value,
       ROUND(AVG(f.value) OVER (ORDER BY f.date_key ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS ma_3m
FROM fact_market_monthly f
JOIN dim_date d USING (date_key)
WHERE f.series_id = 'sx5e'
ORDER BY f.date_key DESC
LIMIT 12;

-- 6. Real policy rate regime: how many months was the real DFR negative?
SELECT CASE WHEN value < 0 THEN 'Negative real rate' ELSE 'Positive real rate' END AS regime,
       COUNT(*) AS months
FROM fact_market_monthly
WHERE series_id = 'real_dfr'
GROUP BY regime;
