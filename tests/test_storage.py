import psycopg2
import pytest

from src.storage import (
    add_product,
    deactivate_product,
    delete_product,
    get_all_products,
    get_connection,
    get_latest_price,
    get_latest_prices,
    get_price_history,
    get_price_series,
    get_product,
    save_price,
    save_scrape_run,
)

pytestmark = pytest.mark.usefixtures("test_db")


def _query(sql: str, params: tuple) -> list[dict]:
    """Run a read-only query directly, to check tables and views."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


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


def test_latest_prices_returns_one_row_per_product():
    first = add_product("GPU", "https://example.com/1", 500.00)
    second = add_product("CPU", "https://example.com/2", 300.00)
    save_price(first["id"], 600.00)
    save_price(first["id"], 550.00)
    save_price(second["id"], 280.00)

    latest = get_latest_prices()

    assert len(latest) == 2
    assert latest[first["id"]]["price"] == 550.00
    assert latest[second["id"]]["price"] == 280.00


def test_latest_prices_ignores_products_without_history():
    add_product("GPU", "https://example.com/1", 500.00)
    assert get_latest_prices() == {}


def test_price_series_is_per_product_and_chronological():
    first = add_product("GPU", "https://example.com/1", 500.00)
    second = add_product("CPU", "https://example.com/2", 300.00)
    save_price(first["id"], 600.00)
    save_price(first["id"], 580.00)
    save_price(second["id"], 290.00)

    series = get_price_series(points=10)

    assert [p["price"] for p in series[first["id"]]] == [600.00, 580.00]
    assert [p["price"] for p in series[second["id"]]] == [290.00]


def test_price_series_limits_per_product():
    product = add_product("GPU", "https://example.com/1", 500.00)
    for price in (600.00, 590.00, 580.00):
        save_price(product["id"], price)

    series = get_price_series(points=2)

    assert len(series[product["id"]]) == 2


# --- Scrape runs ---


def test_scrape_runs_keep_failures():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_scrape_run(product["id"], "ok", 599.90, 1200)
    save_scrape_run(product["id"], "blocked", None, 300)

    rows = _query(
        "SELECT status, price FROM scrape_run WHERE product_id = %s ORDER BY id",
        (product["id"],),
    )

    assert [row["status"] for row in rows] == ["ok", "blocked"]
    assert rows[1]["price"] is None


# --- Data quality views ---


def test_quality_view_computes_success_rate():
    product = add_product("GPU", "https://www.example.com/gpu", 500.00)
    save_scrape_run(product["id"], "ok", 599.90, 1000)
    save_scrape_run(product["id"], "ok", 599.90, 1200)
    save_scrape_run(product["id"], "blocked", None, 300)

    rows = _query("SELECT * FROM v_scrape_quality WHERE product_id = %s", (product["id"],))

    assert rows[0]["site"] == "www.example.com"
    assert rows[0]["attempts"] == 3
    assert rows[0]["successes"] == 2
    assert float(rows[0]["success_rate_pct"]) == 66.7


def test_quality_view_keeps_products_without_attempts():
    product = add_product("GPU", "https://example.com/gpu", 500.00)

    rows = _query("SELECT * FROM v_scrape_quality WHERE product_id = %s", (product["id"],))

    assert rows[0]["attempts"] == 0
    assert rows[0]["success_rate_pct"] is None


def test_price_changes_view_flags_suspicious_jumps():
    product = add_product("GPU", "https://example.com/gpu", 500.00)
    save_price(product["id"], 100.00)
    save_price(product["id"], 100.00)
    save_price(product["id"], 150.00)

    rows = _query("SELECT * FROM v_price_changes WHERE product_id = %s", (product["id"],))

    assert len(rows) == 1
    assert float(rows[0]["change_pct"]) == 50.0
    assert rows[0]["is_suspicious"] is True
