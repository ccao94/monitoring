from fastapi import FastAPI, HTTPException

from src.storage import init_db, get_all_products, get_product, get_price_history

app = FastAPI(title="Price Monitor API")


@app.on_event("startup")
def startup():
    init_db()


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