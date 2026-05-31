# Price Monitor

Automated price tracker for hardware and tech products. Scrapes product pages, stores price history, and sends Telegram alerts when prices drop below a set threshold.

Runs automatically every 6 hours via GitHub Actions — no server needed.

## How it works

1. Products to monitor are listed in `products.json` (URL + price threshold)
2. A Python scraper fetches each product page and extracts the current price (JSON-LD structured data, regex fallback)
3. Prices are saved in a SQLite database for history tracking
4. If a price drops below the threshold, a Telegram message is sent
5. GitHub Actions runs the scraper on a schedule (every 6h) and persists the database as an artifact

## Stack

- **Python 3.12** — scraper, API, storage
- **FastAPI** — REST API for managing products and viewing price history
- **SQLite** — price history storage
- **Telegram Bot API** — price drop notifications
- **Docker** — containerized app
- **GitHub Actions** — CI (tests + Docker build) and scheduled scraper
- **Kubernetes / Minikube** — CronJob deployment (local demo)
- **PyTest** — unit tests with mocking

## Project structure

```
monitoring/
├── src/
│   ├── api.py          # FastAPI endpoints (CRUD products, price history)
│   ├── scraper.py      # price extraction (JSON-LD + regex fallback)
│   ├── storage.py      # SQLite operations (products, price history)
│   ├── alerting.py     # Telegram bot notifications
│   ├── sync.py         # sync products.json → database
│   └── config.py       # env vars, HTTP headers
├── tests/
│   ├── test_scraper.py
│   ├── test_alerting.py
│   └── test_storage.py
├── k8s/
│   ├── cronjob.yml     # Kubernetes CronJob manifest
│   └── secret.yml      # Kubernetes secret (Telegram credentials)
├── .github/workflows/
│   ├── ci.yml          # tests + Docker build on push
│   └── scraper.yml     # scheduled price checks (every 6h)
├── products.json       # products to monitor
├── Dockerfile
├── main.py             # entry point
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.12+
- A Telegram bot (create one via [@BotFather](https://t.me/BotFather))

### Install

```bash
git clone https://github.com/ccao94/monitoring.git
cd monitoring
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configure

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Run

```bash
# Run the scraper once
python main.py

# Start the API (product management + price history)
uvicorn src.api:app --reload
# Then open http://127.0.0.1:8000/docs
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

Supported sites: any e-commerce site that includes JSON-LD product data (LDLC, Amazon, Fnac, most major retailers).

## Tests

```bash
pytest -v
```

## Docker

```bash
docker build -t price-monitor .
docker run --env-file .env price-monitor
```