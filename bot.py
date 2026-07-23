import requests

from src.alerting import send_telegram_message
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.scraper import get_price
from src.storage import get_all_products, init_db, save_price

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
            "/list — show all monitored products\n"
            "/check — check all prices now"
        )

    elif command in ("/watch", "/remove"):
        return (
            "Products are managed in <code>products.json</code>.\n"
            "Edit the file, commit and push — the next run picks it up."
        )

    elif command == "/list":
        products = get_all_products()
        if not products:
            return "No products monitored."
        lines = []
        for p in products:
            lines.append(
                f"<b>[{p['id']}]</b> {p['name']}\n    Alert below {p['alert_below']:.2f} €"
            )
        return "\n\n".join(lines)

    elif command == "/check":
        products = get_all_products()
        if not products:
            return "No products to check."
        results = []
        for p in products:
            result = get_price(p["url"])
            if result.status == "ok":
                save_price(p["id"], result.price)
                line = f"✅ {p['name']}: <b>{result.price:.2f} €</b>"
                if result.price < p["alert_below"]:
                    line += " 📉 BELOW THRESHOLD!"
                results.append(line)
            else:
                results.append(f"❌ {p['name']}: {result.status}")
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
