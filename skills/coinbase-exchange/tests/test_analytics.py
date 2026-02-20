import pathlib
import sys
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

from analytics import atr, ema, realized_volatility_from_candles, rsi  # noqa: E402


class AnalyticsMathTests(unittest.TestCase):
    def test_realized_volatility_positive(self) -> None:
        candles = [
            [1, 90, 110, 100, 100, 10],
            [2, 95, 115, 105, 105, 11],
            [3, 100, 120, 110, 110, 12],
            [4, 105, 125, 115, 120, 13],
        ]
        self.assertGreater(realized_volatility_from_candles(candles), 0.0)

    def test_ema(self) -> None:
        series = ema([1, 2, 3, 4, 5], period=3)
        self.assertEqual(len(series), 5)
        self.assertGreater(series[-1], series[0])

    def test_rsi_range(self) -> None:
        value = rsi([1, 1.2, 1.4, 1.5, 1.6, 1.55, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.1, 2.2, 2.25])
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 100.0)

    def test_atr(self) -> None:
        candles = [[i, 90 + i, 100 + i, 95 + i, 97 + i, 10] for i in range(1, 40)]
        self.assertGreater(atr(candles, period=14), 0.0)


if __name__ == "__main__":
    unittest.main()
