import psycopg2
import pytest

from src.storage import (
    add_product,
    deactivate_product,
    delete_product,
    get_all_products,
    get_latest_price,
    get_price_history,
    get_product,
    save_price,
)

pytestmark = pytest.mark.usefixtures("test_db")


# --- Products ---


def test_add_and_get_product():
    product = add_product("GPU Test", "https://example.com/gpu", 500.00)
    assert product["name"] == "GPU Test"
    fetched = get_product(product["id"])
    assert fetched["url"] == "https://example.com/gpu"
    assert fetched["alert_below"] == 500.00


def test_duplicate_url_raises():
    add_product("GPU", "https://example.com/gpu", 500.00)
    with pytest.raises(psycopg2.IntegrityError):
        add_product("GPU again", "https://example.com/gpu", 400.00)


def test_list_active_products():
    add_product("GPU 1", "https://example.com/1", 500.00)
    add_product("GPU 2", "https://example.com/2", 600.00)
    assert len(get_all_products(active_only=True)) == 2


def test_deactivate_product():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    deactivate_product(product["id"])
    assert len(get_all_products(active_only=True)) == 0
    assert len(get_all_products(active_only=False)) == 1


def test_delete_product():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    assert delete_product(product["id"]) is True
    assert get_product(product["id"]) is None


def test_delete_nonexistent():
    assert delete_product(999) is False


def test_delete_cascades_price_history():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_price(product["id"], 599.90)
    delete_product(product["id"])
    assert get_price_history(product["id"]) == []


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
