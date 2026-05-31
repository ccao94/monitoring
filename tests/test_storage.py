import os
import sqlite3
from src.storage import init_db, save_price, get_latest_price, get_price_history

TEST_DB = "test_prices.db"


def setup_function():
    """Use a test database before each test."""
    import src.storage
    src.storage.DB_PATH = TEST_DB
    init_db()


def teardown_function():
    """Clean up test database after each test."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_save_and_get_latest():
    save_price("GPU Test", "https://example.com", 599.90)
    assert get_latest_price("GPU Test") == 599.90


def test_latest_returns_most_recent():
    save_price("GPU Test", "https://example.com", 599.90)
    save_price("GPU Test", "https://example.com", 549.90)
    assert get_latest_price("GPU Test") == 549.90


def test_unknown_product_returns_none():
    assert get_latest_price("Unknown Product") is None


def test_price_history():
    save_price("GPU", "https://example.com", 600.00)
    save_price("GPU", "https://example.com", 580.00)
    save_price("GPU", "https://example.com", 550.00)
    history = get_price_history("GPU", limit=2)
    assert len(history) == 2
    assert history[0]["price"] == 550.00  # most recent first