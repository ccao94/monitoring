from src.scraper import parse_price_from_jsonld, parse_price_from_html


class TestParseJsonLd:
    def test_valid_product(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Product", "name": "GPU Test", "offers": {"price": 659.90, "priceCurrency": "EUR"}}
        </script>
        </head><body></body></html>
        """
        assert parse_price_from_jsonld(html) == 659.90

    def test_price_as_string(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Product", "name": "GPU", "offers": {"price": "499.99"}}
        </script>
        </head><body></body></html>
        """
        assert parse_price_from_jsonld(html) == 499.99

    def test_offers_as_list(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Product", "name": "GPU", "offers": [{"price": 299.90}]}
        </script>
        </head><body></body></html>
        """
        assert parse_price_from_jsonld(html) == 299.90

    def test_no_product_returns_none(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "WebSite", "name": "LDLC"}
        </script>
        </head><body></body></html>
        """
        assert parse_price_from_jsonld(html) is None

    def test_no_jsonld_returns_none(self):
        html = "<html><head></head><body>Hello</body></html>"
        assert parse_price_from_jsonld(html) is None


class TestParseHtml:
    def test_price_with_euro_sign(self):
        html = '<span class="price">659€90</span>'
        assert parse_price_from_html(html) == 659.90

    def test_price_with_spaces(self):
        html = '<span>1 299€95</span>'
        assert parse_price_from_html(html) == 1299.95

    def test_no_price_returns_none(self):
        html = "<html><body>No price here</body></html>"
        assert parse_price_from_html(html) is None