from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.storage import (
    init_db,
    add_product,
    get_all_products,
    get_product,
    delete_product,
    get_price_history,
)

app = FastAPI(title="Price Monitor API")


class ProductCreate(BaseModel):
    name: str
    url: str
    alert_below: float


@app.on_event("startup")
def startup():
    init_db()


@app.get("/products")
def list_products():
    return get_all_products()


@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    try:
        return add_product(product.name, product.url, product.alert_below)
    except Exception:
        raise HTTPException(status_code=400, detail="Product with this URL already exists")


@app.get("/products/{product_id}")
def read_product(product_id: int):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}")
def remove_product(product_id: int):
    if not delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product deleted"}


@app.get("/products/{product_id}/history")
def read_price_history(product_id: int, limit: int = 10):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_price_history(product_id, limit)