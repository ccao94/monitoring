import sqlite3
from datetime import datetime

DB_PATH = "prices.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            alert_below REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            checked_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.commit()
    conn.close()


# --- Products ---

def add_product(name: str, url: str, alert_below: float) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, url, alert_below, created_at) VALUES (?, ?, ?, ?)",
        (name, url, alert_below, datetime.now().isoformat()),
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return {"id": product_id, "name": name, "url": url, "alert_below": alert_below}


def get_all_products(active_only: bool = True) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM products WHERE active = 1")
    else:
        cursor.execute("SELECT * FROM products")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_product(product_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_product(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def deactivate_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# --- Price history ---

def save_price(product_id: int, price: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (product_id, price, checked_at) VALUES (?, ?, ?)",
        (product_id, price, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_latest_price(product_id: int) -> float | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT 1",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row["price"] if row else None


def get_price_history(product_id: int, limit: int = 10) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price, checked_at FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT ?",
        (product_id, limit),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows