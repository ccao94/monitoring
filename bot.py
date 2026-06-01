import time

import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.storage import init_db, add_product, get_all_products, delete_product, save_price
from src.scraper import get_price
from src.alerting import send_telegram_message


BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def get_updates(offset=None):
    """Long-poll Telegram for new messages."""
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return response.json().get("result", [])
    except requests.RequestException:
        return []


def handle_command(text: str) -> str:
    """Parse a command and return a response string."""
    parts = text.strip().split()
    command = parts[0].lower().split("@")[0]  # ignore @botname suffix

    if command == "/start":
        return (
            "🔍 <b>Price Monitor Bot</b>\n\n"
            "<b>Commands:</b>\n"
            "/watch &lt;url&gt; &lt;price&gt; &lt;name&gt; — add a product\n"
            "/list — show all monitored products\n"
            "/remove &lt;id&gt; — remove a product\n"
            "/check — check all prices now"
        )

    elif command == "/watch":
        if len(parts) < 4:
            return "Usage: /watch &lt;url&gt; &lt;alert_price&gt; &lt;product name&gt;"
        url = parts[1]
        try:
            alert_below = float(parts[2])
        except ValueError:
            return "Price must be a number."
        name = " ".join(parts[3:])
        try:
            add_product(name, url, alert_below)
            return f"✅ Added: <b>{name}</b>\nAlert below: {alert_below:.2f} €"
        except Exception:
            return "❌ A product with this URL already exists."

    elif command == "/list":
        products = get_all_products()
        if not products:
            return "No products monitored."
        lines = []
        for p in products:
            lines.append(
                f"<b>[{p['id']}]</b> {p['name']}\n"
                f"    Alert below {p['alert_below']:.2f} €"
            )
        return "\n\n".join(lines)

    elif command == "/remove":
        if len(parts) < 2:
            return "Usage: /remove &lt;id&gt;"
        try:
            product_id = int(parts[1])
        except ValueError:
            return "ID must be a number."
        if delete_product(product_id):
            return f"✅ Product {product_id} removed."
        return "❌ Product not found."

    elif command == "/check":
        products = get_all_products()
        if not products:
            return "No products to check."
        results = []
        for p in products:
            try:
                price = get_price(p["url"])
                if price is not None:
                    save_price(p["id"], price)
                    line = f"✅ {p['name']}: <b>{price:.2f} €</b>"
                    if price < p["alert_below"]:
                        line += " 📉 BELOW THRESHOLD!"
                    results.append(line)
                else:
                    results.append(f"❌ {p['name']}: could not get price")
            except Exception as e:
                results.append(f"❌ {p['name']}: error")
        return "\n\n".join(results)

    return "Unknown command. Try /start"


def main():
    init_db()
    print("Bot started. Listening for commands...")
    print("Press Ctrl+C to stop.\n")
    offset = None

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            if not text or chat_id != int(TELEGRAM_CHAT_ID):
                continue

            print(f"Received: {text}")
            response = handle_command(text)
            send_telegram_message(response)


if __name__ == "__main__":
    main()