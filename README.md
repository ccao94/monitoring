# Price Monitor

**Live dashboard:** https://price-monitor-gj4e.onrender.com
(free hosting, the first request after inactivity takes about a minute)

Price tracker for tech products. It scrapes product pages, stores the price history in
PostgreSQL, and sends a Telegram alert when a price crosses below a threshold or drops by
10% or more. Every scrape attempt is logged, and SQL views turn that journal into data
quality indicators.

## Stack

Python 3.12, FastAPI, PostgreSQL (Neon), Telegram Bot API, PyTest, Ruff, Docker,
GitHub Actions, Kubernetes (Minikube). Dashboard deployed on Render.

## Run locally

Prerequisites: Python 3.12+, Docker, a PostgreSQL database and a Telegram bot.

```bash
pip install -r requirements-dev.txt
python main.py                  # one run: sync products, fetch prices, send alerts
uvicorn src.api:app --reload    # read-only API and dashboard
```

Configuration comes from a `.env` file, never committed:

```
DATABASE_URL=postgresql://user:password@host/db?sslmode=require
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

Tracked products are listed in `products.json` (URL and alert threshold).

## Tests

```bash
docker compose up -d test-db
pytest
```

61 tests, run against a real PostgreSQL instance rather than mocks, including the SQL
views. GitHub Actions runs lint, tests and the Docker build on every push.

## Design notes

**`products.json` is the single source of truth.** The database is a derived state, rebuilt
on every run. The API and the Telegram bot are read-only, so the desired state stays
versioned in Git.

**Prices come from structured data only.** The scraper reads JSON-LD and microdata, never
raw HTML. A regex on markup silently picks up struck-through prices, and a wrong price is
worse than no price.

**Bot walls are detected.** Some sites answer HTTP 200 with a captcha page instead of the
product. A page that is too small, or shows bot-check wording, is reported as blocked
instead of "no price found".

**Alerts fire on transitions.** A product sitting below its threshold does not send a
message on every run, only the crossing does.

**Failures are visible.** Each scrape returns a typed status. If every product fails, the
run exits non-zero so the job turns red instead of passing silently.

**Data quality is measured, not assumed.** Every attempt is logged in `scrape_run`,
successful or not, separately from the clean price history. SQL views compute the success
rate per site, freshness, completeness and suspicious price changes. Calculation rules are
defined once in `src/views.sql` and documented in [docs/kpi.md](docs/kpi.md).

## Where it runs

Scheduled runs on GitHub Actions were disabled: the failure check above revealed that
retailers block datacenter IP ranges, so every cloud run was refused. Collection now runs
every hour from a residential connection, through a Windows scheduled task
(`scripts/run_scraper.ps1`). A Kubernetes CronJob version is kept in `k8s/`. The dashboard
stays online and reads the shared database.