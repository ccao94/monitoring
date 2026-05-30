from src.scraper import get_price
from src.storage import init_db, save_price, get_price_history
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

        if price < product["alert_below"]:
            print(f"  -> ALERT: below {product['alert_below']:.2f} EUR!")

        # Show recent history
        history = get_price_history(product["name"], limit=5)
        if len(history) > 1:
            print(f"  -> History ({len(history)} entries):")
            for entry in history:
                print(f"     {entry['checked_at']} : {entry['price']:.2f} EUR")


if __name__ == "__main__":
    main()