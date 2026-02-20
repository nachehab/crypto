import os

os.environ["COINBASE_MARKETS_CACHE"] = "/tmp/coinbase_markets_cache_test.json"

from scripts.coinbase_analysis import analyze_markets, realized_volatility, top_movers


class MockConnector:
    def __init__(self):
        self.products = [
            {"id": "AAA-USD", "base_currency": "AAA", "quote_currency": "USD", "status": "online", "base_min_size": "0.1"},
            {"id": "BBB-USD", "base_currency": "BBB", "quote_currency": "USD", "status": "online", "base_min_size": "0.1"},
            {"id": "CCC-USD", "base_currency": "CCC", "quote_currency": "USD", "status": "online", "base_min_size": "0.1"},
        ]

    def list_products(self):
        return self.products

    def product_ticker(self, product_id):
        prices = {"AAA-USD": "11", "BBB-USD": "8", "CCC-USD": "6"}
        return {"price": prices[product_id]}

    def product_stats(self, product_id):
        stats = {
            "AAA-USD": {"open": "10", "volume": "1200"},
            "BBB-USD": {"open": "10", "volume": "1800"},
            "CCC-USD": {"open": "5", "volume": "900"},
        }
        return stats[product_id]

    def product_book(self, product_id, level=2):
        return {
            "bids": [["10", "100"], ["9.9", "40"]],
            "asks": [["10.1", "110"], ["10.2", "30"]],
        }

    def product_candles(self, product_id, granularity, limit=200):
        base = {"AAA-USD": 10.0, "BBB-USD": 8.0, "CCC-USD": 5.0}[product_id]
        out = []
        for i in range(limit):
            close = base + (i * 0.02)
            out.append([1700000000 + i * granularity, close - 0.1, close + 0.1, close - 0.05, close, 100 + i])
        return out


def test_top_movers_sorting():
    result = top_movers(MockConnector(), quote_currency="USD", limit=2)
    gainers = result["data"]["gainers"]
    assert gainers[0]["product_id"] == "CCC-USD"
    assert gainers[1]["product_id"] == "AAA-USD"


def test_realized_volatility_synthetic():
    candles = [[i, 0, 0, 0, 100 + i * 2, 1] for i in range(1, 50)]
    vol = realized_volatility(candles)
    assert vol > 0


def test_analyze_markets_schema():
    result = analyze_markets(MockConnector(), quote="USD", window="24h", limit=3)
    market = result["data"]["markets"][0]
    expected = {"product_id", "base", "quote", "price", "change_pct", "volume", "volatility", "spread", "trend_label", "notes"}
    assert expected.issubset(set(market.keys()))


def test_analyze_markets_integration_order():
    result = analyze_markets(MockConnector(), quote="USD", window="24h", limit=2)
    assert len(result["data"]["markets"]) == 2
    assert result["summary"].startswith("Scanned")
