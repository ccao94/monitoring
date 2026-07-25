"""Check whether a product URL can be scraped, before adding it to products.json.

Usage: python check_url.py <url>
"""

import sys

from src.scraper import fetch_page, parse_price_from_jsonld, parse_price_from_meta

EXPLANATIONS = {
    "not_found": "Page does not exist. Check the URL.",
    "blocked": "Site refused the request. It may block automated traffic.",
    "network_error": "Could not reach the site after retries.",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    url = sys.argv[1]
    print(f"Fetching {url}\n")

    status, html = fetch_page(url)
    if status != "ok":
        print(f"FAILED: {EXPLANATIONS.get(status, status)}")
        return 1

    print(f"Page fetched ({len(html)} chars)\n")

    sources = {
        "JSON-LD": parse_price_from_jsonld(html),
        "microdata / Open Graph": parse_price_from_meta(html),
    }

    for name, price in sources.items():
        mark = "OK  " if price is not None else "none"
        value = f"{price:.2f} EUR" if price is not None else "-"
        print(f"  {mark} {name:<24} {value}")

    if any(price is not None for price in sources.values()):
        print("\nThis URL can be monitored.")
        return 0

    print("\nNo structured price data. This URL cannot be monitored as-is.")
    return 1


if __name__ == "__main__":
    sys.exit(main())