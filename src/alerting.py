import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


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
        f"<a href=\"{url}\">View on LDLC</a>"
    )
    send_telegram_message(message)