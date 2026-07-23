from datetime import UTC, datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from src.config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            alert_below NUMERIC(10, 2) NOT NULL,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            price NUMERIC(10, 2) NOT NULL,
            checked_at TIMESTAMPTZ NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# --- Products ---


def add_product(name: str, url: str, alert_below: float) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO products (name, url, alert_below, created_at)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, url, alert_below
        """,
        (name, url, alert_below, datetime.now(UTC)),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "alert_below": float(row["alert_below"]),
    }


def get_all_products(active_only: bool = True) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM products WHERE active = TRUE ORDER BY id")
    else:
        cursor.execute("SELECT * FROM products ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [_product_to_dict(row) for row in rows]


def get_product(product_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return _product_to_dict(row) if row else None


def delete_product(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def deactivate_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET active = FALSE WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()


# --- Price history ---


def save_price(product_id: int, price: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (product_id, price, checked_at) VALUES (%s, %s, %s)",
        (product_id, price, datetime.now(UTC)),
    )
    conn.commit()
    conn.close()


def get_latest_price(product_id: int) -> float | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM price_history WHERE product_id = %s ORDER BY checked_at DESC LIMIT 1",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return float(row["price"]) if row else None


def get_price_history(product_id: int, limit: int = 10) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT price, checked_at FROM price_history
        WHERE product_id = %s ORDER BY checked_at DESC LIMIT %s
        """,
        (product_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"price": float(row["price"]), "checked_at": row["checked_at"].isoformat()} for row in rows
    ]


def _product_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "alert_below": float(row["alert_below"]),
        "active": row["active"],
        "created_at": row["created_at"].isoformat(),
    }


def get_latest_prices() -> dict[int, dict]:
    """Latest price for every product, in a single query.

    DISTINCT ON keeps the first row per product_id, and the ORDER BY
    decides which one that is.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ON (product_id) product_id, price, checked_at
        FROM price_history
        ORDER BY product_id, checked_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return {
        row["product_id"]: {
            "price": float(row["price"]),
            "checked_at": row["checked_at"],
        }
        for row in rows
    }
