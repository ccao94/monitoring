import json

from src.storage import init_db, add_product, get_all_products, delete_product

PRODUCTS_FILE = "products.json"


def sync_products():
    """Sync products from products.json into the database."""
    init_db()

    with open(PRODUCTS_FILE, "r") as f:
        desired = json.load(f)

    desired_urls = {p["url"] for p in desired}
    existing = get_all_products(active_only=False)
    existing_urls = {p["url"] for p in existing}

    # Add new products
    for product in desired:
        if product["url"] not in existing_urls:
            add_product(product["name"], product["url"], product["alert_below"])
            print(f"  Added: {product['name']}")

    # Remove products no longer in the file
    for product in existing:
        if product["url"] not in desired_urls:
            delete_product(product["id"])
            print(f"  Removed: {product['name']}")