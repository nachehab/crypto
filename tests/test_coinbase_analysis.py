import json
import os
import threading
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["COINBASE_MARKETS_CACHE"] = "/tmp/coinbase_markets_cache_test.json"

from scripts.coinbase_analysis import (
    CoinbaseConnector,
    analyze_markets,
    atr,
    ema,
    realized_volatility,
    rsi,
    top_movers,
)


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


def test_trend_metrics_computation():
    closes = [100 + i for i in range(60)]
    ema_vals = ema(closes, 20)
    assert len(ema_vals) == len(closes)
    assert rsi(closes) > 50

    candles = [[i, 99 + i, 101 + i, 100 + i, 100 + i, 1] for i in range(30)]
    assert atr(candles) > 0


def test_analyze_markets_schema():
    result = analyze_markets(MockConnector(), quote="USD", window="24h", limit=3)
    market = result["data"]["markets"][0]
    expected = {
        "product_id",
        "base",
        "quote",
        "price",
        "change_pct",
        "volume",
        "volatility",
        "spread",
        "trend_label",
        "notes",
        "reasons",
    }
    assert expected.issubset(set(market.keys()))


def test_analyze_markets_integration_order():
    result = analyze_markets(MockConnector(), quote="USD", window="24h", limit=2)
    assert len(result["data"]["markets"]) == 2
    assert result["summary"].startswith("Scanned")


def test_http_integration_with_mock_server(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/products":
                payload = [{"id": "AAA-USD", "base_currency": "AAA", "quote_currency": "USD", "status": "online"}]
            elif self.path == "/orders":
                payload = [{"id": "1"}]
                self.send_response(200)
                self.send_header("cb-after", "cursor-1")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())
                return
            elif self.path == "/orders?after=cursor-1":
                payload = [{"id": "2"}]
            else:
                payload = {"ok": True}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    from scripts import coinbase_analysis

    monkeypatch.setattr(coinbase_analysis, "EXCHANGE_API", f"http://127.0.0.1:{server.server_port}")

    conn = CoinbaseConnector(timeout=2)
    products = conn.list_products()
    pages = conn.get_paginated("/orders")

    server.shutdown()

    assert products[0]["id"] == "AAA-USD"
    assert [row["id"] for row in pages] == ["1", "2"]
