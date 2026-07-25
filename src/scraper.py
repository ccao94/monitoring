import json
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from src.config import HEADERS

MAX_RETRIES = 3
RETRY_DELAY = 2
TIMEOUT = 15
MAX_PLAUSIBLE_PRICE = 100_000
MIN_PAGE_SIZE = 5000
BLOCK_MARKERS = (
    "captcha",
    "unusual traffic",
    "are you a human",
    "enable javascript",
    "access denied",
)


@dataclass
class ScrapeResult:
    """Outcome of a scrape attempt.

    status is one of: ok, not_found, blocked, network_error, parse_error
    """

    status: str
    price: float | None = None
    detail: str = ""


def _to_float(raw) -> float | None:
    """Convert a price string to float. Handles '1 299,95 €' and '659.90'."""
    if raw is None:
        return None
    text = str(raw).strip()
    for char in ("\xa0", "\u202f", " ", "€", "EUR"):
        text = text.replace(char, "")
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def looks_blocked(html: str) -> bool:
    """Detect a 200 response that is really a bot-check page.

    Product pages are large. A short body, or bot-check wording near the
    top, means the site answered with a wall instead of the product.
    """
    if len(html) < MIN_PAGE_SIZE:
        return True
    head = html[:4000].lower()
    return any(marker in head for marker in BLOCK_MARKERS)


def fetch_page(url: str) -> tuple[str, str | None]:
    """Fetch a product page. Returns (status, html).

    Retries on network errors and 5xx, never on 404 or 403.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return "network_error", None

        if response.status_code in (404, 410):
            return "not_found", None

        if response.status_code in (401, 403, 429):
            return "blocked", None

        if response.status_code >= 500:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return "network_error", None

        if looks_blocked(response.text):
            return "blocked", None

        return "ok", response.text

    return "network_error", None


def parse_price_from_jsonld(html: str) -> float | None:
    """Extract price from JSON-LD structured data."""
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            if not isinstance(offers, dict):
                continue
            price = _to_float(offers.get("price"))
            if price is not None:
                return price

    return None


def parse_price_from_meta(html: str) -> float | None:
    """Extract price from microdata or Open Graph meta tags."""
    soup = BeautifulSoup(html, "html.parser")
    candidates = [
        {"itemprop": "price"},
        {"property": "product:price:amount"},
        {"property": "og:price:amount"},
    ]

    for attrs in candidates:
        element = soup.find("meta", attrs=attrs)
        if element and element.get("content"):
            price = _to_float(element["content"])
            if price is not None:
                return price

    return None


def is_plausible(price: float) -> bool:
    return 0 < price < MAX_PLAUSIBLE_PRICE


def get_price(url: str) -> ScrapeResult:
    """Fetch a product page and extract its price."""
    status, html = fetch_page(url)
    if status != "ok":
        return ScrapeResult(status=status)

    for parser in (parse_price_from_jsonld, parse_price_from_meta):
        price = parser(html)
        if price is None:
            continue
        if not is_plausible(price):
            return ScrapeResult("parse_error", detail=f"implausible price: {price}")
        return ScrapeResult("ok", price=price)

    return ScrapeResult("parse_error", detail="no structured price data found")
