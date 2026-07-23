from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.storage import (
    get_all_products,
    get_latest_prices,
    get_price_history,
    get_product,
    init_db,
)


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


@app.get("/", response_class=HTMLResponse)
def dashboard():
    products = get_all_products()
    latest = get_latest_prices()

    rows = []
    for product in products:
        current = latest.get(product["id"])
        if current is None:
            price_cell = "<td>—</td><td>—</td>"
        else:
            below = current["price"] < product["alert_below"]
            colour = "#1a7f37" if below else "#24292f"
            price_cell = (
                f'<td style="color:{colour};font-weight:600">'
                f"{current['price']:.2f} €</td>"
                f"<td>{current['checked_at']:%Y-%m-%d %H:%M} UTC</td>"
            )
        rows.append(
            f"<tr>"
            f'<td><a href="{product["url"]}">{product["name"]}</a></td>'
            f"{price_cell}"
            f"<td>{product['alert_below']:.2f} €</td>"
            f'<td><a href="/products/{product["id"]}/history">history</a></td>'
            f"</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Price Monitor</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px;
           margin: 3rem auto; padding: 0 1rem; color: #24292f; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
    th, td {{ text-align: left; padding: 0.6rem 0.8rem;
              border-bottom: 1px solid #d0d7de; }}
    th {{ font-size: 0.8rem; text-transform: uppercase; color: #656d76; }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    footer {{ margin-top: 2rem; font-size: 0.85rem; color: #656d76; }}
  </style>
</head>
<body>
  <h1>Price Monitor</h1>
  <p>Tracking {len(products)} products. Prices refresh every 6 hours.</p>
  <table>
    <tr><th>Product</th><th>Current</th><th>Last check</th>
        <th>Alert below</th><th></th></tr>
    {"".join(rows)}
  </table>
  <footer>
    <a href="/docs">API docs</a> ·
    <a href="https://github.com/ccao94/monitoring">Source</a>
  </footer>
</body>
</html>"""
