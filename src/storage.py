import sqlite3
from datetime import datetime


DB_PATH = "prices.db"


def init_db():
    """Create the prices table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            url TEXT NOT NULL,
            price REAL NOT NULL,
            checked_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_price(product_name: str, url: str, price: float):
    """Save a price entry with current timestamp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (product_name, url, price, checked_at) VALUES (?, ?, ?, ?)",
        (product_name, url, price, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_latest_price(product_name: str) -> float | None:
    """Get the most recent price for a product."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM price_history WHERE product_name = ? ORDER BY checked_at DESC LIMIT 1",
        (product_name,),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_price_history(product_name: str, limit: int = 10) -> list[dict]:
    """Get recent price entries for a product."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price, checked_at FROM price_history WHERE product_name = ? ORDER BY checked_at DESC LIMIT ?",
        (product_name, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"price": row[0], "checked_at": row[1]} for row in rows]