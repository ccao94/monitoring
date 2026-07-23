import sys

from src.alerting import (
    decide_alert,
    send_price_alert,
    send_price_drop,
    send_telegram_message,
)
from src.scraper import get_price
from src.storage import (
    deactivate_product,
    get_all_products,
    get_latest_price,
    init_db,
    save_price,
)
from src.sync import sync_products

STATUS_MESSAGES = {
    "not_found": "Page no longer exists (404).",
    "blocked": "Site refused the request (403/429).",
    "network_error": "Network error after retries.",
    "parse_error": "No price found on the page.",
}


def main() -> int:
    init_db()
    sync_products()

    products = get_all_products()
    if not products:
        print("No products to monitor.")
        return 0

    failures = 0

    for product in products:
        print(f"Checking: {product['name']}")
        result = get_price(product["url"])

        if result.status == "ok":
            previous = get_latest_price(product["id"])
            save_price(product["id"], result.price)
            print(f"  -> {result.price:.2f} EUR (saved)")

            threshold = product["alert_below"]
            decision = decide_alert(previous, result.price, threshold)

            if decision == "threshold":
                print(f"  -> ALERT: crossed below {threshold:.2f} EUR")
                send_price_alert(product["name"], result.price, threshold, product["url"])
            elif decision == "drop":
                print(f"  -> ALERT: dropped from {previous:.2f} EUR")
                send_price_drop(product["name"], previous, result.price, product["url"])
            continue

        failures += 1
        reason = STATUS_MESSAGES.get(result.status, result.status)
        print(f"  -> FAILED: {reason} {result.detail}".rstrip())

        if result.status == "not_found":
            deactivate_product(product["id"])
            send_telegram_message(
                f"⚠️ <b>Dead link</b>\n\n{product['name']}\n{reason} Product deactivated."
            )

    if failures == len(products):
        send_telegram_message(
            f"🚨 <b>Monitoring failed</b>\n\n"
            f"All {failures} products failed to update. Check the workflow logs."
        )
        return 1

    print(f"\nDone. {len(products) - failures}/{len(products)} products updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
