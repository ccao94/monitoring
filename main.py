from src.scraper import get_price
from src.storage import init_db, get_all_products, save_price, deactivate_product
from src.alerting import send_price_alert, send_telegram_message


def main():
    init_db()
    products = get_all_products()

    if not products:
        print("No products to monitor. Add some via the API.")
        return

    for product in products:
        print(f"Checking: {product['name']}")
        try:
            price = get_price(product["url"])
        except Exception as e:
            print(f"  -> Error: {e}")
            # Notify and deactivate if the page is gone
            if "404" in str(e):
                send_telegram_message(
                    f"⚠️ <b>Dead link</b>\n\n"
                    f"{product['name']}\n"
                    f"URL no longer available. Product deactivated."
                )
                deactivate_product(product["id"])
            continue

        if price is None:
            print("  -> Could not retrieve price")
            continue

        save_price(product["id"], price)
        print(f"  -> Current price: {price:.2f} EUR (saved)")

        if price < product["alert_below"]:
            print(f"  -> ALERT: below {product['alert_below']:.2f} EUR!")
            send_price_alert(
                product["name"], price, product["alert_below"], product["url"]
            )


if __name__ == "__main__":
    main()