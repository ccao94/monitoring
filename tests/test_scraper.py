from unittest.mock import patch, MagicMock

import requests

from src.scraper import (
    _to_float,
    fetch_page,
    get_price,
    parse_price_from_jsonld,
    parse_price_from_meta,
)


def _response(status_code: int, text: str = ""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    return mock


class TestToFloat:
    def test_plain_decimal(self):
        assert _to_float("659.90") == 659.90

    def test_french_comma(self):
        assert _to_float("659,90") == 659.90

    def test_spaces_and_currency(self):
        assert _to_float(" 1 299,95 € ") == 1299.95

    def test_garbage_returns_none(self):
        assert _to_float("n/a") is None

    def test_none_returns_none(self):
        assert _to_float(None) is None


class TestParseJsonLd:
    def test_valid_product(self):
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "offers": {"price": 659.90, "priceCurrency": "EUR"}}
        </script>
        """
        assert parse_price_from_jsonld(html) == 659.90

    def test_price_as_string(self):
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "offers": {"price": "499.99"}}
        </script>
        """
        assert parse_price_from_jsonld(html) == 499.99

    def test_offers_as_list(self):
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "offers": [{"price": 299.90}]}
        </script>
        """
        assert parse_price_from_jsonld(html) == 299.90

    def test_ignores_non_product(self):
        html = """
        <script type="application/ld+json">
        {"@type": "WebSite", "name": "LDLC"}
        </script>
        """
        assert parse_price_from_jsonld(html) is None

    def test_malformed_json_is_skipped(self):
        html = """
        <script type="application/ld+json">{not valid json</script>
        <script type="application/ld+json">
        {"@type": "Product", "offers": {"price": 100.00}}
        </script>
        """
        assert parse_price_from_jsonld(html) == 100.00

    def test_no_jsonld(self):
        assert parse_price_from_jsonld("<html><body>hi</body></html>") is None


class TestParseMeta:
    def test_itemprop_price(self):
        assert parse_price_from_meta('<meta itemprop="price" content="659.90">') == 659.90

    def test_og_price(self):
        html = '<meta property="og:price:amount" content="1299,95">'
        assert parse_price_from_meta(html) == 1299.95

    def test_no_meta(self):
        assert parse_price_from_meta("<html></html>") is None


class TestFetchPage:
    @patch("src.scraper.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = _response(200, "<html>ok</html>")
        status, html = fetch_page("https://example.com")
        assert status == "ok"
        assert html == "<html>ok</html>"

    @patch("src.scraper.requests.get")
    def test_404_is_not_retried(self, mock_get):
        mock_get.return_value = _response(404)
        status, _ = fetch_page("https://example.com")
        assert status == "not_found"
        assert mock_get.call_count == 1

    @patch("src.scraper.requests.get")
    def test_403_is_blocked(self, mock_get):
        mock_get.return_value = _response(403)
        status, _ = fetch_page("https://example.com")
        assert status == "blocked"

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.requests.get")
    def test_server_error_is_retried(self, mock_get, mock_sleep):
        mock_get.return_value = _response(503)
        status, _ = fetch_page("https://example.com")
        assert status == "network_error"
        assert mock_get.call_count == 3

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.requests.get")
    def test_recovers_after_transient_error(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            requests.Timeout("timed out"),
            _response(200, "<html>ok</html>"),
        ]
        status, html = fetch_page("https://example.com")
        assert status == "ok"
        assert mock_get.call_count == 2


class TestGetPrice:
    @patch("src.scraper.fetch_page")
    def test_returns_price(self, mock_fetch):
        mock_fetch.return_value = ("ok", '<meta itemprop="price" content="659.90">')
        result = get_price("https://example.com")
        assert result.status == "ok"
        assert result.price == 659.90

    @patch("src.scraper.fetch_page")
    def test_propagates_fetch_status(self, mock_fetch):
        mock_fetch.return_value = ("not_found", None)
        assert get_price("https://example.com").status == "not_found"

    @patch("src.scraper.fetch_page")
    def test_no_structured_data(self, mock_fetch):
        mock_fetch.return_value = ("ok", "<html><body>no price</body></html>")
        assert get_price("https://example.com").status == "parse_error"

    @patch("src.scraper.fetch_page")
    def test_rejects_implausible_price(self, mock_fetch):
        mock_fetch.return_value = ("ok", '<meta itemprop="price" content="0">')
        assert get_price("https://example.com").status == "parse_error"