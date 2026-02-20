import os
from typing import Any, Dict

from analytics import analyze_markets as analyze_markets_impl
from analytics import liquidity_snapshot as liquidity_snapshot_impl
from analytics import top_movers as top_movers_impl
from analytics import trend_signal as trend_signal_impl
from analytics import volatility_rank as volatility_rank_impl
from client import CoinbaseExchangeClient, CoinbaseExchangeError
from markets import list_markets as list_markets_impl
from schema import result


REQUIRED_ENV = ["COINBASE_API_KEY", "COINBASE_API_SECRET"]


def _client() -> CoinbaseExchangeClient:
    return CoinbaseExchangeClient()


def coinbase_doctor() -> Dict[str, Any]:
    checks = []
    hints = []
    client = _client()
    env_ok = True
    for var in REQUIRED_ENV:
        exists = bool(os.getenv(var))
        checks.append({"name": var, "ok": exists})
        if not exists:
            env_ok = False
            hints.append(f"Set {var} in skills.entries.coinbase-exchange.env")

    try:
        _, _ = client.request("GET", "/time")
        checks.append({"name": "public_api_connectivity", "ok": True})
    except CoinbaseExchangeError as exc:
        checks.append({"name": "public_api_connectivity", "ok": False, "detail": str(exc)})

    if env_ok:
        try:
            _, _ = client.request("GET", "/accounts", auth=True)
            checks.append({"name": "auth_check", "ok": True})
        except CoinbaseExchangeError as exc:
            checks.append({"name": "auth_check", "ok": False, "detail": str(exc)})
            hints.append("Verify API key, secret, and permissions for Coinbase Advanced Trade REST")
    else:
        checks.append({"name": "auth_check", "ok": False, "detail": "Skipped because credentials missing"})

    ok = all(check.get("ok") for check in checks if check["name"] != "auth_check") and env_ok
    return result(ok, "Coinbase doctor checks completed", checks=checks, hints=hints)


def list_markets(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    items = list_markets_impl(
        client,
        quote_currency=args.get("quote_currency"),
        status=args.get("status"),
        limit=int(args.get("limit", 100)),
    )
    return result(True, f"Found {len(items)} markets", items=items)


def top_movers(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    items = top_movers_impl(
        client,
        window=args.get("window", "24h"),
        quote_currency=args.get("quote_currency", "USD"),
        limit=int(args.get("limit", 20)),
        min_volume=float(args.get("min_volume", 0.0)),
    )
    return result(True, f"Ranked {len(items)} movers", items=items)


def volatility_rank(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    items = volatility_rank_impl(
        client,
        window=args.get("window", "24h"),
        quote_currency=args.get("quote_currency", "USD"),
        limit=int(args.get("limit", 20)),
        min_candles=int(args.get("min_candles", 20)),
    )
    return result(True, f"Ranked {len(items)} markets by volatility", items=items)


def liquidity_snapshot(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    items = liquidity_snapshot_impl(
        client,
        quote_currency=args.get("quote_currency", "USD"),
        limit=int(args.get("limit", 20)),
    )
    return result(True, f"Generated liquidity snapshot for {len(items)} markets", items=items)


def trend_signal(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    item = trend_signal_impl(
        client,
        product_id=args["product_id"],
        timeframe=args.get("timeframe", "4h"),
    )
    return result(True, f"Trend for {item['product_id']} is {item['trend_label']}", item=item)


def analyze_markets(args: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    summary, items = analyze_markets_impl(
        client,
        quote_currency=args.get("quote_currency", "USD"),
        window=args.get("window", "24h"),
        limit=int(args.get("limit", 20)),
        min_volume=float(args.get("min_volume", 0.0)),
    )
    return result(True, summary, items=items)
