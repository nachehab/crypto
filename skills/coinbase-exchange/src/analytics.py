import math
import statistics
from typing import Any, Dict, List, Tuple

from client import CoinbaseExchangeClient
from markets import list_markets


WINDOW_TO_GRANULARITY = {"1h": 300, "4h": 900, "24h": 3600, "1d": 3600}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def realized_volatility_from_candles(candles: List[List[float]]) -> float:
    closes = [c[4] for c in candles if len(c) >= 5 and c[4] > 0]
    if len(closes) < 2:
        return 0.0
    returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(returns) < 2:
        return abs(returns[0]) if returns else 0.0
    return statistics.pstdev(returns) * math.sqrt(len(returns))


def ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append((alpha * value) + ((1 - alpha) * out[-1]))
    return out


def rsi(values: List[float], period: int = 14) -> float:
    if len(values) <= period:
        return 50.0
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(candles: List[List[float]], period: int = 14) -> float:
    if len(candles) <= period:
        return 0.0
    trs: List[float] = []
    for i in range(1, len(candles)):
        high = candles[i][2]
        low = candles[i][1]
        prev_close = candles[i - 1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs[-period:]) / period if trs else 0.0


def top_movers(client: CoinbaseExchangeClient, window: str, quote_currency: str, limit: int, min_volume: float = 0.0) -> List[Dict[str, Any]]:
    markets = list_markets(client, quote_currency=quote_currency, status="online", limit=500)
    movers: List[Dict[str, Any]] = []
    for market in markets:
        product_id = market["product_id"]
        stats, _ = client.request("GET", f"/products/{product_id}/stats")
        open_price = _safe_float(stats.get("open"))
        last_price = _safe_float(stats.get("last"))
        volume = _safe_float(stats.get("volume"))
        if open_price <= 0 or volume < min_volume:
            continue
        change_pct = ((last_price - open_price) / open_price) * 100
        movers.append(
            {
                "product_id": product_id,
                "base": market["base"],
                "quote": market["quote"],
                "price": last_price,
                "change_pct": change_pct,
                "volume": volume,
                "reasons": [f"{window} change {change_pct:.2f}%", f"volume {volume:.2f}"],
            }
        )
    movers.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return movers[:limit]


def volatility_rank(
    client: CoinbaseExchangeClient,
    window: str,
    quote_currency: str,
    limit: int,
    min_candles: int = 20,
) -> List[Dict[str, Any]]:
    granularity = WINDOW_TO_GRANULARITY.get(window, 3600)
    markets = list_markets(client, quote_currency=quote_currency, status="online", limit=500)
    ranked: List[Dict[str, Any]] = []
    for market in markets:
        candles, _ = client.request("GET", f"/products/{market['product_id']}/candles", params={"granularity": granularity})
        if not isinstance(candles, list) or len(candles) < min_candles:
            continue
        candles = sorted(candles, key=lambda c: c[0])
        vol = realized_volatility_from_candles(candles)
        ranked.append({"product_id": market["product_id"], "volatility": vol, "candles": len(candles)})
    ranked.sort(key=lambda x: x["volatility"], reverse=True)
    return ranked[:limit]


def liquidity_snapshot(client: CoinbaseExchangeClient, quote_currency: str, limit: int) -> List[Dict[str, Any]]:
    markets = list_markets(client, quote_currency=quote_currency, status="online", limit=500)
    snapshots: List[Dict[str, Any]] = []
    for market in markets[:limit]:
        book, _ = client.request("GET", f"/products/{market['product_id']}/book", params={"level": 2})
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        if not bids or not asks:
            continue
        best_bid = _safe_float(bids[0][0])
        best_ask = _safe_float(asks[0][0])
        spread = best_ask - best_bid if best_ask and best_bid else 0.0
        depth_top = sum(_safe_float(level[1]) for level in bids[:5]) + sum(_safe_float(level[1]) for level in asks[:5])
        snapshots.append(
            {
                "product_id": market["product_id"],
                "spread": spread,
                "depth_top": depth_top,
                "notes": ["level2 order book", "depth is top 5 bid/ask sizes"],
            }
        )
    snapshots.sort(key=lambda x: x["depth_top"], reverse=True)
    return snapshots[:limit]


def trend_signal(client: CoinbaseExchangeClient, product_id: str, timeframe: str) -> Dict[str, Any]:
    granularity = WINDOW_TO_GRANULARITY.get(timeframe, 3600)
    candles, _ = client.request("GET", f"/products/{product_id}/candles", params={"granularity": granularity})
    candles = sorted(candles, key=lambda c: c[0])
    closes = [_safe_float(c[4]) for c in candles]
    if not closes:
        return {"product_id": product_id, "trend_label": "neutral", "rsi": 50.0, "ema_slope": 0.0, "atr": 0.0}
    ema_series = ema(closes, period=21)
    ema_slope = ema_series[-1] - ema_series[max(0, len(ema_series) - 2)] if len(ema_series) > 1 else 0.0
    rsi_value = rsi(closes, period=14)
    atr_value = atr(candles, period=14)
    label = "neutral"
    if rsi_value > 55 and ema_slope > 0:
        label = "bullish"
    elif rsi_value < 45 and ema_slope < 0:
        label = "bearish"
    return {
        "product_id": product_id,
        "trend_label": label,
        "rsi": round(rsi_value, 2),
        "ema_slope": round(ema_slope, 8),
        "atr": round(atr_value, 8),
    }


def analyze_markets(
    client: CoinbaseExchangeClient,
    quote_currency: str = "USD",
    window: str = "24h",
    limit: int = 20,
    min_volume: float = 0.0,
) -> Tuple[str, List[Dict[str, Any]]]:
    movers = top_movers(client, window=window, quote_currency=quote_currency, limit=limit, min_volume=min_volume)
    vol_map = {item["product_id"]: item for item in volatility_rank(client, window=window, quote_currency=quote_currency, limit=limit)}
    liq_map = {item["product_id"]: item for item in liquidity_snapshot(client, quote_currency=quote_currency, limit=limit)}
    items: List[Dict[str, Any]] = []
    for mover in movers:
        product_id = mover["product_id"]
        trend = trend_signal(client, product_id=product_id, timeframe="4h")
        items.append(
            {
                **mover,
                "volatility": vol_map.get(product_id, {}).get("volatility"),
                "spread": liq_map.get(product_id, {}).get("spread"),
                "trend_label": trend.get("trend_label"),
                "notes": liq_map.get(product_id, {}).get("notes", []),
            }
        )
    bullish = sum(1 for item in items if item.get("trend_label") == "bullish")
    summary = f"Analyzed {len(items)} {quote_currency} markets; {bullish} bullish on 4h trend." if items else "No markets matched filters."
    return summary, items
