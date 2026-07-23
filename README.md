# Price Monitor

Automated price tracker for hardware and tech products. Scrapes product pages, stores price history, and sends Telegram alerts when prices drop below a set threshold.

Runs automatically every 6 hours via GitHub Actions - no server needed.

**Live dashboard:** https://price-monitor-gj4e.onrender.com

Hosted on a free tier - the first request after a period of inactivity takes
about a minute to wake the service.

## How it works

1. Products to monitor are listed in `products.json` (URL + price threshold)
2. A Python scraper fetches each product page and extracts the current price from structured data (JSON-LD, then microdata / Open Graph)
3. Prices are stored in a hosted PostgreSQL database for history tracking
4. A Telegram message is sent when a price crosses below its threshold, or drops by 10% or more
5. GitHub Actions runs the scraper every 6 hours against the same database

## Stack

- **Python 3.12** - scraper, API, storage
- **FastAPI** - read-only REST API for products and price history
- **PostgreSQL (Neon)** - hosted database for products and price history
- **Telegram Bot API** - price drop notifications and on-demand checks
- **Docker** - containerized app, plus a local Postgres for tests
- **GitHub Actions** - CI (lint, tests, Docker build) and scheduled scraper
- **Kubernetes / Minikube** - CronJob deployment (local demo)
- **PyTest** - 48 tests, run against a real database
- **Ruff** - linting and formatting, enforced in CI
- **Render** - hosted API and dashboard, deployed from render.yaml

## Project structure

```
monitoring/
├── src/
│   ├── api.py          # FastAPI read-only endpoints (products, price history)
│   ├── scraper.py      # price extraction (JSON-LD, then microdata)
│   ├── storage.py      # PostgreSQL operations (products, price history)
│   ├── alerting.py     # Telegram notifications, alert decision logic
│   ├── sync.py         # sync products.json → database
│   └── config.py       # env vars, HTTP headers
├── tests/
│   ├── conftest.py         # test database fixture
│   ├── test_scraper.py
│   ├── test_alerting.py
│   ├── test_alert_logic.py
│   ├── test_storage.py
│   └── test_main.py
├── k8s/
│   ├── cronjob.yml            # Kubernetes CronJob manifest
│   └── secret.example.yml     # secret template (Telegram + database)
├── .github/workflows/
│   ├── ci.yml          # lint, tests and Docker build on push
│   └── scraper.yml     # scheduled price checks (every 6h)
├── products.json           # products to monitor
├── main.py                 # entry point, one scraping run
├── bot.py                  # interactive Telegram bot (optional, runs locally)
├── docker-compose.yml      # local Postgres for tests
├── pyproject.toml          # ruff and pytest configuration
├── Dockerfile
├── requirements.txt        # runtime dependencies
└── requirements-dev.txt    # runtime + pytest + ruff
```

## Setup

### Prerequisites

- Python 3.12+
- Docker (for the test database)
- A PostgreSQL database — [Neon](https://neon.tech) has a free tier
- A Telegram bot (create one via [@BotFather](https://t.me/BotFather))

### Install

```bash
git clone https://github.com/ccao94/monitoring.git
cd monitoring
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### Configure

Create a `.env` file:

```
DATABASE_URL=postgresql://user:password@host/db?sslmode=require
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Run

```bash
# One scraping run: sync products, fetch prices, send alerts
python main.py

# Read-only API
uvicorn src.api:app --reload
# Then open http://127.0.0.1:8000/docs

# Interactive Telegram bot (/list, /check)
python bot.py
```

## Adding products

Edit `products.json`:

```json
[
  {
    "name": "Product Name",
    "url": "https://www.ldlc.com/fiche/PBxxxxxxxx.html",
    "alert_below": 500.00
  }
]
```

Commit and push. The next scheduled run picks up the changes automatically.

Supported sites: any e-commerce site exposing JSON-LD or microdata product info (LDLC, Amazon, Fnac, most major retailers).

## Tests

Tests run against a real PostgreSQL instance, not a mock:

```bash
docker compose up -d test-db
pytest -v
```

Lint and formatting, same commands as CI:

```bash
ruff check .
ruff format --check .
```

## Docker

```bash
docker build -t price-monitor .
docker run --env-file .env price-monitor
```

## Kubernetes (local demo)

```bash
minikube start
minikube docker-env | Invoke-Expression   # PowerShell
docker build -t price-monitor:latest .
kubectl create secret generic telegram-credentials --from-env-file=.env
kubectl apply -f k8s/cronjob.yml
```

The CronJob writes to the same database as GitHub Actions. Suspend one of the
two if you don't want duplicate readings:

```bash
kubectl patch cronjob price-monitor -p '{"spec":{"suspend":true}}'
```

## Design notes

**`products.json` is the single source of truth.** The database is a derived
state, rebuilt on every run. Adding or removing a product means editing the
file and pushing - the API and Telegram bot are read-only. This keeps the
desired state versioned in Git.

**Prices come from structured data only.** The scraper reads JSON-LD and
microdata, never raw HTML. Regex on markup silently picks up struck-through
prices and sidebar listings, and a wrong price is worse than no price.

**Alerts fire on transitions, not states.** A product sitting below its
threshold does not send a message every six hours - only the crossing does.

**Failures are visible.** Each scrape returns a typed status (`ok`,
`not_found`, `blocked`, `network_error`, `parse_error`). Dead links deactivate
the product and notify. If every product fails, the run exits non-zero so the
workflow turns red instead of passing silently.