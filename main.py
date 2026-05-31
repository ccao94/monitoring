from src.scraper import get_price
from src.storage import init_db, save_price, get_price_history
from src.alerting import send_telegram_message, send_price_alert
from src.config import PRODUCTS


def main():
    init_db()

    for product in PRODUCTS:
        print(f"Checking: {product['name']}")
        price = get_price(product["url"])

        if price is None:
            print("  -> Could not retrieve price")
            continue

        save_price(product["name"], product["url"], price)
        print(f"  -> Current price: {price:.2f} EUR (saved)")

        # Alert if price drops below threshold
        if price < product["alert_below"]:
            print(f"  -> ALERT: below {product['alert_below']:.2f} EUR!")
            send_price_alert(product["name"], price, product["alert_below"], product["url"])

        # Show recent history
        history = get_price_history(product["name"], limit=5)
        if len(history) > 1:
            print(f"  -> History ({len(history)} entries):")
            for entry in history:
                print(f"     {entry['checked_at']} : {entry['price']:.2f} EUR")


if __name__ == "__main__":
    main()