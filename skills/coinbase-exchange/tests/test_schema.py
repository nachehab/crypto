import pathlib
import sys
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

from schema import normalize_market, validate_market  # noqa: E402


class SchemaTests(unittest.TestCase):
    def test_normalize_market(self) -> None:
        item = normalize_market(
            {
                "id": "BTC-USD",
                "base_currency": "BTC",
                "quote_currency": "USD",
                "status": "online",
                "base_min_size": "0.0001",
                "quote_increment": "0.01",
                "base_increment": "0.00000001",
            }
        )
        self.assertEqual(item["product_id"], "BTC-USD")
        self.assertEqual(item["base"], "BTC")

    def test_validate_market_missing(self) -> None:
        with self.assertRaises(ValueError):
            validate_market({"product_id": "BTC-USD"})


if __name__ == "__main__":
    unittest.main()
