# Data quality indicators

Indicators are computed once, in SQL views (`src/views.sql`), and read by every consumer
(dashboard, reports). A rule changes in one place only.

## Collection success rate

- **Definition:** share of scrape attempts that returned a price.
- **Rule:** `successes / attempts × 100`, per product, all attempts since the journal started
  (`v_scrape_quality.success_rate_pct`).
- **Reading:** below 100%, look at the failure status in `scrape_run`. `blocked` means the
  site refused the request, `network_error` means it never answered.
- **Limit:** a product with no attempt yet has no rate (`NULL`), not 0%.

## Average attempt duration

- **Definition:** mean time spent on one attempt, retries included (`avg_duration_ms`).
- **Reading:** around 51,000 ms means three timeouts of 15 s plus the pauses between them:
  the site leaves the connection hanging rather than refusing it.

## Freshness

- **Definition:** hours since the last successful price (`hours_since_success`).
- **Reading:** collection runs every hour, so a value above 3 means the price shown is
  outdated. An empty value means the product has never been collected successfully.

## Collection completeness

- **Definition:** share of hours, since the first run, in which at least one collection ran
  (`v_collection_completeness.completeness_pct`).
- **Reading:** collection runs from a personal computer, so gaps match the hours it was off.
- **Limit:** several runs in the same hour count once.

## Suspicious price changes

- **Definition:** a price change of more than 30% between two consecutive readings
  (`v_price_changes.is_suspicious`).
- **Reading:** not necessarily an error, a sale can reach 30%, but worth a manual check.
  A wrong reading, such as an accessory price picked instead of the product, shows up here.
- **Limit:** the 30% threshold is a choice, not a standard. It can be adjusted once enough
  real price changes have been observed.