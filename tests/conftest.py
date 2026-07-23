import os

import pytest

import src.storage
from src.storage import init_db, get_connection

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://monitoring:monitoring@localhost:5433/monitoring_test",
)


@pytest.fixture
def test_db(monkeypatch):
    """Point storage at the test database and clean up after each test."""
    monkeypatch.setattr(src.storage, "DATABASE_URL", TEST_DATABASE_URL)
    init_db()
    yield
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE price_history, products RESTART IDENTITY CASCADE")
    conn.commit()
    conn.close()