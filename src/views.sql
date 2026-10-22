-- Data quality per product: reliability and freshness
CREATE OR REPLACE VIEW v_scrape_quality AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    split_part(p.url, '/', 3) AS site,
    COUNT(r.id) AS attempts,
    COUNT(r.id) FILTER (WHERE r.status = 'ok') AS successes,
    ROUND(100.0 * COUNT(r.id) FILTER (WHERE r.status = 'ok')
          / NULLIF(COUNT(r.id), 0), 1) AS success_rate_pct,
    ROUND(AVG(r.duration_ms)) AS avg_duration_ms,
    MAX(r.checked_at) AS last_attempt_at,
    MAX(r.checked_at) FILTER (WHERE r.status = 'ok') AS last_success_at,
    ROUND(EXTRACT(EPOCH FROM now() - MAX(r.checked_at) FILTER (WHERE r.status = 'ok'))
          / 3600, 1) AS hours_since_success
FROM products p
LEFT JOIN scrape_run r ON r.product_id = p.id
WHERE p.active
GROUP BY p.id, p.name, p.url;

-- Collection completeness: share of hours with at least one run
CREATE OR REPLACE VIEW v_collection_completeness AS
SELECT
    MIN(checked_at) AS first_run_at,
    COUNT(DISTINCT date_trunc('hour', checked_at)) AS hours_with_run,
    CEIL(EXTRACT(EPOCH FROM now() - MIN(checked_at)) / 3600) AS hours_elapsed,
    ROUND(100.0 * COUNT(DISTINCT date_trunc('hour', checked_at))
          / NULLIF(CEIL(EXTRACT(EPOCH FROM now() - MIN(checked_at)) / 3600), 0), 1)
          AS completeness_pct
FROM scrape_run;

-- Price changes between consecutive readings, with a plausibility flag
CREATE OR REPLACE VIEW v_price_changes AS
SELECT
    product_id,
    product_name,
    checked_at,
    previous_price,
    price,
    ROUND(100.0 * (price - previous_price) / previous_price, 1) AS change_pct,
    ABS(price - previous_price) > 0.3 * previous_price AS is_suspicious
FROM (
    SELECT
        h.product_id,
        p.name AS product_name,
        h.checked_at,
        h.price,
        LAG(h.price) OVER (PARTITION BY h.product_id ORDER BY h.checked_at) AS previous_price
    FROM price_history h
    JOIN products p ON p.id = h.product_id
) readings
WHERE previous_price IS NOT NULL
  AND price <> previous_price;