from contextlib import asynccontextmanager
from datetime import UTC, datetime
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.storage import (
    get_all_products,
    get_latest_prices,
    get_price_history,
    get_price_series,
    get_product,
    init_db,
)

CHART_WIDTH = 240
CHART_HEIGHT = 56


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Price Monitor API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def list_products():
    return get_all_products()


@app.get("/products/{product_id}")
def read_product(product_id: int):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/{product_id}/history")
def read_price_history(product_id: int, limit: int = 10):
    if not get_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return get_price_history(product_id, limit)


FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2'
    "?family=Archivo:wght@400;600;800"
    '&family=IBM+Plex+Mono:wght@400;500&display=swap">'
)

STYLES = """
<style>
  :root {
    --paper: #e8eaed;
    --card: #fcfcfd;
    --ink: #13171c;
    --muted: #6f7883;
    --rule: #d3d8de;
    --line: #3d4956;
    --below: #0d6b3d;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    padding: 4rem 1.25rem 5rem;
    background: var(--paper);
    color: var(--ink);
    font-family: Archivo, system-ui, sans-serif;
    font-variant-numeric: tabular-nums;
  }

  main { max-width: 780px; margin: 0 auto; }

  h1 {
    margin: 0;
    font-size: clamp(1.9rem, 6vw, 2.9rem);
    font-weight: 800;
    font-stretch: 125%;
    letter-spacing: -0.01em;
    text-transform: uppercase;
  }

  .status {
    margin: 0.6rem 0 2.5rem;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.02em;
  }

  .row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 1.5rem;
    align-items: center;
    padding: 1.4rem 1.5rem;
    background: var(--card);
    border: 1px solid var(--rule);
    border-radius: 3px;
    margin-bottom: 0.6rem;
  }

  .name {
    display: block;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--ink);
    text-decoration: none;
    margin-bottom: 0.5rem;
    max-width: 34ch;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .name:hover { text-decoration: underline; }

  .price {
    font-family: "IBM Plex Mono", monospace;
    font-size: 1.75rem;
    font-weight: 500;
    letter-spacing: -0.02em;
  }

  .price.below { color: var(--below); }

  .gap {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.76rem;
    color: var(--muted);
    margin-top: 0.35rem;
  }

  .gap strong { color: var(--below); font-weight: 500; }

  .chart { width: 240px; }
  .chart svg { display: block; width: 100%; height: auto; }

  .pending {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.72rem;
    color: var(--muted);
    text-align: right;
    margin: 0;
    width: 240px;
  }

  .empty {
    padding: 2.5rem 1.5rem;
    background: var(--card);
    border: 1px dashed var(--rule);
    font-size: 0.9rem;
    color: var(--muted);
  }

  footer {
    margin-top: 2.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--rule);
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.76rem;
    color: var(--muted);
  }

  footer a { color: var(--ink); }

  a:focus-visible, .name:focus-visible {
    outline: 2px solid var(--ink);
    outline-offset: 3px;
  }

  @media (max-width: 620px) {
    .row { grid-template-columns: 1fr; gap: 1rem; }
    .chart, .pending { width: 100%; }
    .name { max-width: 100%; }
  }
</style>
"""


def _chart(series: list[dict], threshold: float) -> str:
    """Render a price line with the alert threshold drawn across it."""
    if len(series) < 2:
        return '<p class="pending">collecting data</p>'

    values = [point["price"] for point in series]
    low = min(min(values), threshold)
    high = max(max(values), threshold)
    padding = (high - low) * 0.15 or 1.0
    low -= padding
    high += padding
    span = high - low

    def y(value: float) -> float:
        return CHART_HEIGHT - (value - low) / span * CHART_HEIGHT

    step = CHART_WIDTH / (len(values) - 1)
    points = " ".join(f"{i * step:.1f},{y(v):.1f}" for i, v in enumerate(values))
    threshold_y = y(threshold)
    last_y = y(values[-1])
    stroke = "var(--below)" if values[-1] < threshold else "var(--line)"

    return (
        f'<svg viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" role="img" '
        f'aria-label="Price history with alert threshold">'
        f'<line x1="0" y1="{threshold_y:.1f}" x2="{CHART_WIDTH}" y2="{threshold_y:.1f}" '
        f'stroke="var(--muted)" stroke-width="1" stroke-dasharray="3 3" '
        f'vector-effect="non-scaling-stroke" />'
        f'<polyline points="{points}" fill="none" stroke="{stroke}" '
        f'stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round" '
        f'vector-effect="non-scaling-stroke" />'
        f'<circle cx="{CHART_WIDTH}" cy="{last_y:.1f}" r="3" fill="{stroke}" />'
        f"</svg>"
    )


def _row(product: dict, current: dict | None, series: list[dict]) -> str:
    name = escape(product["name"])
    url = escape(product["url"], quote=True)
    threshold = product["alert_below"]

    if current is None:
        price_html = '<div class="price">—</div>'
        gap_html = '<div class="gap">no reading yet</div>'
    else:
        price = current["price"]
        below = price < threshold
        classes = "price below" if below else "price"
        price_html = f'<div class="{classes}">{price:.2f} €</div>'
        if below:
            gap_html = f'<div class="gap"><strong>under target</strong> · {threshold:.2f} €</div>'
        else:
            over = (price - threshold) / threshold * 100
            gap_html = f'<div class="gap">{over:.0f}% above target · {threshold:.2f} €</div>'

    return (
        f'<article class="row">'
        f"<div>"
        f'<a class="name" href="{url}">{name}</a>'
        f"{price_html}{gap_html}"
        f"</div>"
        f'<div class="chart">{_chart(series, threshold)}</div>'
        f"</article>"
    )


@app.get("/", response_class=HTMLResponse)
def dashboard():
    products = get_all_products()
    latest = get_latest_prices()
    series = get_price_series()

    if products:
        body = "".join(
            _row(product, latest.get(product["id"]), series.get(product["id"], []))
            for product in products
        )
    else:
        body = (
            '<div class="empty">No products tracked yet. '
            "Add one to <code>products.json</code> and push.</div>"
        )

    checks = [entry["checked_at"] for entry in latest.values()]
    if checks:
        newest = max(checks)
        stamp = newest.strftime("%d %b %Y, %H:%M UTC").lower()
        hours = int((datetime.now(UTC) - newest).total_seconds() // 3600)
        freshness = "just now" if hours < 1 else f"{hours}h ago"
        status = f"{len(products)} tracked · last check {stamp} · {freshness}"
    else:
        status = f"{len(products)} tracked · no checks recorded"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price Monitor</title>
{FONTS}
{STYLES}
</head>
<body>
<main>
  <h1>Price Monitor</h1>
  <p class="status">{status} · checks every 6h</p>
  {body}
  <footer>
    Dashed line marks the alert threshold ·
    <a href="/docs">API</a> ·
    <a href="https://github.com/ccao94/monitoring">Source</a>
  </footer>
</main>
</body>
</html>"""
