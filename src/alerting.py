import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

SIGNIFICANT_DROP = 0.10  # alert on drops of 10% or more


def decide_alert(previous: float | None, current: float, threshold: float) -> str | None:
    """Decide whether a price change is worth an alert.

    Returns "threshold" when the price crosses below the alert threshold,
    "drop" for a significant decrease that stays above it, None otherwise.
    """
    crossed = current < threshold and (previous is None or previous >= threshold)
    if crossed:
        return "threshold"

    if previous is not None and current < previous * (1 - SIGNIFICANT_DROP):
        return "drop"

    return None


def send_telegram_message(message: str) -> bool:
    """Send a message via Telegram bot. Returns True if successful."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Telegram credentials not configured, skipping alert")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Failed to send Telegram alert: {e}")
        return False


def send_price_alert(product_name: str, price: float, threshold: float, url: str):
    """Send a formatted price drop alert."""
    message = (
        f"📉 <b>Price Alert</b>\n\n"
        f"<b>{product_name}</b>\n"
        f"Current price: <b>{price:.2f} €</b>\n"
        f"Your threshold: {threshold:.2f} €\n\n"
        f'<a href="{url}">View on LDLC</a>'
    )
    send_telegram_message(message)


def send_price_drop(product_name: str, old_price: float, new_price: float, url: str):
    """Send an alert for a significant price drop."""
    diff = old_price - new_price
    percent = (diff / old_price) * 100
    message = (
        f"📉 <b>Price drop</b>\n\n"
        f"<b>{product_name}</b>\n"
        f"{old_price:.2f} € → <b>{new_price:.2f} €</b>\n"
        f"-{diff:.2f} € (-{percent:.1f}%)\n\n"
        f'<a href="{url}">View product</a>'
    )
    send_telegram_message(message)
