import os
from src.storage import (
    init_db,
    add_product,
    get_all_products,
    get_product,
    delete_product,
    deactivate_product,
    save_price,
    get_latest_price,
    get_price_history,
)
import src.storage

TEST_DB = "test_prices.db"


def setup_function():
    src.storage.DB_PATH = TEST_DB
    init_db()


def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# --- Products ---

def test_add_and_get_product():
    product = add_product("GPU Test", "https://example.com/gpu", 500.00)
    assert product["name"] == "GPU Test"
    fetched = get_product(product["id"])
    assert fetched["url"] == "https://example.com/gpu"


def test_list_active_products():
    add_product("GPU 1", "https://example.com/1", 500.00)
    add_product("GPU 2", "https://example.com/2", 600.00)
    products = get_all_products(active_only=True)
    assert len(products) == 2


def test_deactivate_product():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    deactivate_product(product["id"])
    active = get_all_products(active_only=True)
    all_products = get_all_products(active_only=False)
    assert len(active) == 0
    assert len(all_products) == 1


def test_delete_product():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    assert delete_product(product["id"]) is True
    assert get_product(product["id"]) is None


def test_delete_nonexistent():
    assert delete_product(999) is False


# --- Prices ---

def test_save_and_get_latest():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_price(product["id"], 599.90)
    assert get_latest_price(product["id"]) == 599.90


def test_latest_returns_most_recent():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_price(product["id"], 599.90)
    save_price(product["id"], 549.90)
    assert get_latest_price(product["id"]) == 549.90


def test_unknown_product_returns_none():
    assert get_latest_price(999) is None


def test_price_history():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_price(product["id"], 600.00)
    save_price(product["id"], 580.00)
    save_price(product["id"], 550.00)
    history = get_price_history(product["id"], limit=2)
    assert len(history) == 2
    assert history[0]["price"] == 550.00