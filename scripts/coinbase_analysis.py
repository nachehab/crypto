#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib import error, parse, request

EXCHANGE_API = "https://api.exchange.coinbase.com"
CACHE_TTL_SECONDS = 300
_TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}


def _cache_path() -> Path:
    return Path(os.environ.get("COINBASE_MARKETS_CACHE", "/tmp/coinbase_markets_cache.json"))


class CoinbaseAPIError(RuntimeError):
    pass


class CoinbaseConnector:
    def __init__(self, timeout: int = 10, throttle_seconds: float = 0.08, max_retries: int = 3):
        self.timeout = timeout
        self.throttle_seconds = throttle_seconds
        self.max_retries = max_retries
        self._last_call = 0.0

    def _sleep_for_throttle(self) -> None:
        gap = time.time() - self._last_call
        if gap < self.throttle_seconds:
            time.sleep(self.throttle_seconds - gap)

    def _auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        key = os.environ.get("COINBASE_API_KEY")
        secret = os.environ.get("COINBASE_API_SECRET")
        passphrase = os.environ.get("COINBASE_PASSPHRASE")
        if not (key and secret and passphrase):
            return {}
        timestamp = str(time.time())
        prehash = f"{timestamp}{method.upper()}{path}{body}"
        try:
            signing_key = base64.b64decode(secret)
        except Exception:
            return {}
        signature = base64.b64encode(hmac.new(signing_key, prehash.encode("utf-8"), hashlib.sha256).digest()).decode("utf-8")
        return {
            "CB-ACCESS-KEY": key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": passphrase,
        }

    def _request_json(self, method: str, path: str, query: Optional[Dict[str, Any]] = None, authenticated: bool = False) -> Tuple[Any, Dict[str, str]]:
        encoded_query = f"?{parse.urlencode(query)}" if query else ""
        url = f"{EXCHANGE_API}{path}{encoded_query}"
        body = ""
        headers = {"Accept": "application/json", "User-Agent": "openclaw-coinbase-cli/1.1"}
        if authenticated:
            headers.update(self._auth_headers(method, path + encoded_query, body))

        for attempt in range(self.max_retries + 1):
            self._sleep_for_throttle()
            req = request.Request(url, headers=headers, method=method.upper())
            try:
                with request.urlopen(req, timeout=self.timeout) as resp:
                    self._last_call = time.time()
                    payload = json.loads(resp.read().decode("utf-8"))
                    return payload, dict(resp.headers.items())
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                if exc.code in _TRANSIENT_HTTP and attempt < self.max_retries:
                    retry_after = float(exc.headers.get("Retry-After", "0") or 0)
                    backoff = max(retry_after, (2**attempt) * 0.25 + random.uniform(0, 0.25))
                    time.sleep(backoff)
                    continue
                raise CoinbaseAPIError(f"HTTP {exc.code} for {path}: {detail[:250]}") from exc
            except error.URLError as exc:
                if attempt < self.max_retries:
                    time.sleep((2**attempt) * 0.25 + random.uniform(0, 0.25))
                    continue
                raise CoinbaseAPIError(f"Network error for {path}: {exc}") from exc

        raise CoinbaseAPIError(f"Request failed after retries: {path}")

    def _get_json(self, path: str, query: Optional[Dict[str, Any]] = None, authenticated: bool = False) -> Any:
        data, _ = self._request_json("GET", path, query=query, authenticated=authenticated)
        return data

    def get_paginated(self, path: str, query: Optional[Dict[str, Any]] = None, max_pages: int = 5) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        cursor_query = dict(query or {})
        for _ in range(max_pages):
            data, headers = self._request_json("GET", path, query=cursor_query)
            if not isinstance(data, list):
                break
            merged.extend(data)
            after = headers.get("cb-after")
            if not after:
                break
            cursor_query["after"] = after
        return merged

    def list_products(self) -> List[Dict[str, Any]]:
        return self._get_json("/products")

    def product_ticker(self, product_id: str) -> Dict[str, Any]:
        return self._get_json(f"/products/{product_id}/ticker")

    def product_stats(self, product_id: str) -> Dict[str, Any]:
        return self._get_json(f"/products/{product_id}/stats")

    def product_book(self, product_id: str, level: int = 2) -> Dict[str, Any]:
        return self._get_json(f"/products/{product_id}/book", query={"level": level})

    def product_candles(self, product_id: str, granularity: int, limit: int = 200) -> List[List[float]]:
        end = int(datetime.now(timezone.utc).timestamp())
        start = end - (granularity * limit)
        rows = self._get_json(
            f"/products/{product_id}/candles",
            query={"granularity": granularity, "start": start, "end": end},
        )
        rows = sorted(rows, key=lambda x: x[0])
        return rows[-limit:]


@dataclass
class TimeWindow:
    label: str
    granularity: int
    bars: int


WINDOWS = {
    "1h": TimeWindow("1h", 300, 12),
    "4h": TimeWindow("4h", 900, 16),
    "24h": TimeWindow("24h", 3600, 24),
    "7d": TimeWindow("7d", 21600, 28),
}


def _load_market_cache() -> Optional[List[Dict[str, Any]]]:
    cache_path = _cache_path()
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text())
        if time.time() - float(payload.get("ts", 0)) <= CACHE_TTL_SECONDS:
            return payload.get("items", [])
    except Exception:
        return None
    return None


def _save_market_cache(items: List[Dict[str, Any]]) -> None:
    _cache_path().write_text(json.dumps({"ts": time.time(), "items": items}))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def ema(values: Iterable[float], period: int) -> List[float]:
    vals = list(values)
    if not vals:
        return []
    alpha = 2 / (period + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append((v - out[-1]) * alpha + out[-1])
    return out


def rsi(values: Iterable[float], period: int = 14) -> float:
    vals = list(values)
    if len(vals) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(vals)):
        delta = vals[i] - vals[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1 + rs))


def atr(candles: List[List[float]], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs = []
    prev_close = candles[0][4]
    for row in candles[1:]:
        high, low, close = row[2], row[1], row[4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
        prev_close = close
    return sum(trs[-period:]) / period


def realized_volatility(candles: List[List[float]]) -> float:
    closes = [_to_float(c[4]) for c in candles]
    if len(closes) < 3:
        return 0.0
    rets = []
    for i in range(1, len(closes)):
        if closes[i - 1] <= 0:
            continue
        rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 2:
        return 0.0
    return statistics.pstdev(rets) * math.sqrt(len(rets))


def list_markets(connector: CoinbaseConnector, quote_currency: str = "USD", status: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    cached = _load_market_cache()
    products = cached if cached is not None else connector.list_products()
    if cached is None:
        _save_market_cache(products)
    markets = []
    for item in products:
        quote = item.get("quote_currency")
        if quote_currency and quote != quote_currency:
            continue
        resolved_status = item.get("status") or ("online" if not item.get("trading_disabled") else "offline")
        if status and resolved_status != status:
            continue
        markets.append(
            {
                "product_id": item.get("id"),
                "base": item.get("base_currency"),
                "quote": quote,
                "status": resolved_status,
                "min_size": item.get("base_min_size") or item.get("min_market_funds"),
                "quote_increment": item.get("quote_increment"),
                "base_increment": item.get("base_increment"),
            }
        )
    markets.sort(key=lambda m: m["product_id"] or "")
    sliced = markets[: max(1, limit)]
    summary = f"{len(sliced)} {quote_currency} markets available"
    return {"summary": summary, "data": sliced}


def _market_snapshot(connector: CoinbaseConnector, market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pid = market["product_id"]
    try:
        ticker = connector.product_ticker(pid)
        stats = connector.product_stats(pid)
    except CoinbaseAPIError:
        return None
    open_p = _to_float(stats.get("open"))
    last = _to_float(ticker.get("price"))
    volume = _to_float(stats.get("volume"))
    change_abs = last - open_p
    change_pct = (change_abs / open_p * 100) if open_p else 0.0
    return {
        "product_id": pid,
        "base": market.get("base"),
        "quote": market.get("quote"),
        "price": last,
        "change_pct": change_pct,
        "change_abs": change_abs,
        "volume": volume,
    }


def top_movers(
    connector: CoinbaseConnector,
    time_window: str = "24h",
    quote_currency: str = "USD",
    limit: int = 10,
    min_volume: float = 0.0,
) -> Dict[str, Any]:
    _ = time_window
    markets = list_markets(connector, quote_currency)["data"]
    rows = []
    for market in markets[: min(120, len(markets))]:
        snap = _market_snapshot(connector, market)
        if snap and snap["volume"] >= min_volume:
            rows.append(snap)
    rows.sort(key=lambda r: (r["change_pct"], r["change_abs"]), reverse=True)
    top_gainers = rows[:limit]
    top_losers = sorted(rows, key=lambda r: r["change_pct"])[:limit]
    summary = f"Top movers scanned across {len(rows)} {quote_currency} markets"
    return {"summary": summary, "data": {"gainers": top_gainers, "losers": top_losers}}


def volatility_rank(
    connector: CoinbaseConnector,
    time_window: str = "24h",
    quote_currency: str = "USD",
    limit: int = 10,
    min_candles: int = 10,
) -> Dict[str, Any]:
    window = WINDOWS.get(time_window, WINDOWS["24h"])
    markets = list_markets(connector, quote_currency)["data"]
    ranks = []
    for market in markets[: min(80, len(markets))]:
        pid = market["product_id"]
        try:
            candles = connector.product_candles(pid, granularity=window.granularity, limit=window.bars)
        except CoinbaseAPIError:
            continue
        if len(candles) < min_candles:
            continue
        vol = realized_volatility(candles)
        last = _to_float(candles[-1][4], 0.0) if candles else 0.0
        ranks.append({"product_id": pid, "base": market.get("base"), "quote": market.get("quote"), "price": last, "volatility": vol})
    ranks.sort(key=lambda r: r["volatility"], reverse=True)
    summary = f"Volatility ranked for {len(ranks)} {quote_currency} markets"
    return {"summary": summary, "data": ranks[:limit]}


def liquidity_snapshot(connector: CoinbaseConnector, quote_currency: str = "USD", limit: int = 10) -> Dict[str, Any]:
    markets = list_markets(connector, quote_currency)["data"]
    rows = []
    for market in markets[: min(80, len(markets))]:
        pid = market["product_id"]
        try:
            book = connector.product_book(pid, level=2)
        except CoinbaseAPIError:
            continue
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        if not bids or not asks:
            continue
        best_bid = _to_float(bids[0][0])
        best_ask = _to_float(asks[0][0])
        mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0
        spread = ((best_ask - best_bid) / mid * 100) if mid else 0.0
        bid_depth = sum(_to_float(row[1]) for row in bids[:10])
        ask_depth = sum(_to_float(row[1]) for row in asks[:10])
        rows.append(
            {
                "product_id": pid,
                "base": market.get("base"),
                "quote": market.get("quote"),
                "price": mid,
                "spread": spread,
                "bid_depth": bid_depth,
                "ask_depth": ask_depth,
                "liquidity_score": bid_depth + ask_depth,
            }
        )
    rows.sort(key=lambda r: (r["spread"], -r["liquidity_score"]))
    summary = f"Liquidity snapshot for {len(rows)} {quote_currency} markets"
    return {"summary": summary, "data": rows[:limit]}


def trend_signal(connector: CoinbaseConnector, product_id: str, timeframe: str = "1h") -> Dict[str, Any]:
    granularity = {"1h": 300, "4h": 900, "1d": 3600}.get(timeframe, 300)
    bars = 80 if timeframe != "1d" else 120
    candles = connector.product_candles(product_id, granularity=granularity, limit=bars)
    if not candles:
        raise CoinbaseAPIError(f"No candles returned for {product_id}")
    closes = [_to_float(c[4]) for c in candles]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema_slope = ema20[-1] - ema20[-5] if len(ema20) >= 5 else 0.0
    rsi_v = rsi(closes)
    atr_v = atr(candles)
    label = "neutral"
    if ema20[-1] > ema50[-1] and ema_slope > 0 and rsi_v > 55:
        label = "bullish"
    elif ema20[-1] < ema50[-1] and ema_slope < 0 and rsi_v < 45:
        label = "bearish"
    payload = {
        "product_id": product_id,
        "base": product_id.split("-")[0],
        "quote": product_id.split("-")[1] if "-" in product_id else "USD",
        "price": closes[-1],
        "change_pct": ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0.0,
        "volume": sum(_to_float(c[5]) for c in candles[-20:]),
        "volatility": realized_volatility(candles),
        "spread": None,
        "trend_label": label,
        "rsi": rsi_v,
        "ema_slope": ema_slope,
        "atr": atr_v,
        "notes": [f"ema_slope={ema_slope:.6f}", f"rsi={rsi_v:.2f}", f"atr={atr_v:.6f}"],
    }
    return {"summary": f"{product_id} {timeframe} trend is {label}", "data": payload}


def multi_timeframe_summary(connector: CoinbaseConnector, product_id: str) -> Dict[str, Any]:
    frames = ["1h", "4h", "1d"]
    signals = {tf: trend_signal(connector, product_id, tf)["data"] for tf in frames}
    labels = [signals[tf]["trend_label"] for tf in frames]
    bullish = labels.count("bullish")
    bearish = labels.count("bearish")
    if bullish > bearish:
        overall = "bullish"
    elif bearish > bullish:
        overall = "bearish"
    else:
        overall = "neutral"
    confidence = round(max(bullish, bearish) / len(labels), 2)
    conflicts = [tf for tf in frames if signals[tf]["trend_label"] != overall]
    return {
        "summary": f"{product_id} MTF signal {overall} ({confidence:.0%} confidence)",
        "data": {"product_id": product_id, "overall": overall, "confidence": confidence, "conflicts": conflicts, "timeframes": signals},
    }


def analyze_markets(
    connector: CoinbaseConnector,
    quote: str = "USD",
    window: str = "24h",
    limit: int = 20,
    min_volume: float = 0.0,
) -> Dict[str, Any]:
    markets = list_markets(connector, quote, limit=250)["data"]
    movers = top_movers(connector, window, quote, limit=max(10, limit), min_volume=min_volume)["data"]
    vol_rank = volatility_rank(connector, window, quote, limit=max(10, limit))["data"]
    liq = liquidity_snapshot(connector, quote, limit=max(10, limit))["data"]

    by_id: Dict[str, Dict[str, Any]] = {}
    for market in markets:
        by_id[market["product_id"]] = {
            "product_id": market["product_id"],
            "base": market.get("base"),
            "quote": market.get("quote"),
            "price": None,
            "change_pct": None,
            "volume": None,
            "volatility": None,
            "spread": None,
            "trend_label": None,
            "notes": [],
            "reasons": [],
            "score": 0.0,
        }

    for row in movers.get("gainers", []) + movers.get("losers", []):
        item = by_id.get(row["product_id"])
        if not item:
            continue
        item["price"] = row["price"]
        item["change_pct"] = row["change_pct"]
        item["volume"] = row["volume"]
        item["score"] += abs(row["change_pct"]) * 0.4
        item["notes"].append("strong mover")
        item["reasons"].append(f"24h change {row['change_pct']:.2f}%")

    for rank, row in enumerate(vol_rank, start=1):
        item = by_id.get(row["product_id"])
        if not item:
            continue
        item["volatility"] = row["volatility"]
        item["score"] += max(0.0, (limit - rank + 1) / limit) * 30
        item["notes"].append("high volatility")
        item["reasons"].append(f"volatility rank #{rank}")

    for row in liq:
        item = by_id.get(row["product_id"])
        if not item:
            continue
        item["spread"] = row["spread"]
        if row["spread"] <= 1.5:
            item["score"] += 20
            item["notes"].append("sufficient liquidity")
            item["reasons"].append(f"tight spread {row['spread']:.3f}%")
        else:
            item["notes"].append("wide spread")

    ranked = sorted(by_id.values(), key=lambda x: x["score"], reverse=True)
    top = ranked[:limit]

    for item in top[: min(5, len(top))]:
        try:
            trend = trend_signal(connector, item["product_id"], timeframe="1h")["data"]
            item["trend_label"] = trend["trend_label"]
            item["notes"].append(f"1h trend {trend['trend_label']}")
        except CoinbaseAPIError:
            pass

    summary = f"Scanned {len(markets)} {quote} markets. Top setup: {top[0]['product_id'] if top else 'n/a'}"
    return {
        "summary": summary,
        "data": {"quote": quote, "window": window, "generated_at": datetime.now(timezone.utc).isoformat(), "markets": top},
    }


def coinbase_doctor(connector: CoinbaseConnector) -> Dict[str, Any]:
    key = os.environ.get("COINBASE_API_KEY")
    secret = os.environ.get("COINBASE_API_SECRET")
    passphrase = os.environ.get("COINBASE_PASSPHRASE")

    auth_mode = "none"
    if key and secret and passphrase:
        auth_mode = "exchange_hmac"
    elif key and secret:
        auth_mode = "partial_credentials"

    checks = []
    try:
        products = connector.list_products()
        checks.append({"name": "public_products", "ok": True, "count": len(products)})
    except CoinbaseAPIError as exc:
        checks.append({"name": "public_products", "ok": False, "error": str(exc)})

    checks.append({"name": "credentials_present", "ok": bool(key and secret), "hint": "COINBASE_API_KEY + COINBASE_API_SECRET"})
    checks.append({"name": "passphrase_present", "ok": bool(passphrase), "hint": "COINBASE_PASSPHRASE required for Exchange private REST"})

    if auth_mode == "exchange_hmac":
        try:
            accounts = connector._get_json("/accounts", authenticated=True)
            checks.append({"name": "private_accounts", "ok": isinstance(accounts, list), "count": len(accounts) if isinstance(accounts, list) else None})
        except CoinbaseAPIError as exc:
            checks.append({"name": "private_accounts", "ok": False, "error": str(exc)})
    else:
        checks.append({"name": "private_accounts", "ok": False, "warning": "Skipped: missing exchange passphrase or complete credentials"})

    ok = all(c.get("ok") for c in checks if c["name"] not in {"private_accounts"})
    summary = f"Coinbase doctor {'passed' if ok else 'failed'} (auth mode: {auth_mode})"
    next_steps = []
    if not passphrase:
        next_steps.append("Set skills.entries.coinbase-market-analyzer.env.COINBASE_PASSPHRASE for Exchange private endpoint checks.")
    if not (key and secret):
        next_steps.append("Set COINBASE_API_KEY and COINBASE_API_SECRET through OpenClaw skills env injection.")
    return {"summary": summary, "data": {"auth_mode": auth_mode, "checks": checks, "next_steps": next_steps}}
