import pathlib
import sys
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

from markets import list_markets  # noqa: E402


class FakeClient:
    def request(self, method, path, params=None, data=None, auth=False):
        _ = (method, path, params, data, auth)
        return [
            {
                "id": "BTC-USD",
                "base_currency": "BTC",
                "quote_currency": "USD",
                "status": "online",
                "base_min_size": "0.0001",
                "quote_increment": "0.01",
                "base_increment": "0.00000001",
            },
            {
                "id": "ETH-EUR",
                "base_currency": "ETH",
                "quote_currency": "EUR",
                "status": "online",
            },
        ], {}


class MarketsTests(unittest.TestCase):
    def test_list_markets_filter(self):
        items = list_markets(FakeClient(), quote_currency="USD", status="online", limit=10)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product_id"], "BTC-USD")


if __name__ == "__main__":
    unittest.main()
