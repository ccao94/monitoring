import json
import re

import requests
from bs4 import BeautifulSoup

from src.config import HEADERS


def fetch_page(url: str) -> str:
    """Fetch a product page and return raw HTML."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_price_from_jsonld(html: str) -> float | None:
    """Try to extract price from JSON-LD structured data."""
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            data = json.loads(script.string)
            # JSON-LD can be a single object or a list
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    offers = item.get("offers", {})
                    # offers can be a dict or a list
                    if isinstance(offers, list):
                        offers = offers[0]
                    price = offers.get("price")
                    if price is not None:
                        return float(price)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue

    return None


def parse_price_from_html(html: str) -> float | None:
    """Fallback: extract price using regex on the raw HTML.

    LDLC displays prices like '659€90' or '659,90 €'.
    """
    # Pattern: digits + € + digits (e.g. 659€90)
    match = re.search(r'(\d[\d\s]*)\s*€\s*(\d{2})', html)
    if match:
        euros = match.group(1).replace(" ", "")
        cents = match.group(2)
        return float(f"{euros}.{cents}")
    return None


def get_price(url: str) -> float | None:
    """Fetch a product page and extract its price."""
    html = fetch_page(url)
    price = parse_price_from_jsonld(html)
    if price is not None:
        return price
    return parse_price_from_html(html)