#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from coinbase_analysis import (
    CoinbaseAPIError,
    CoinbaseConnector,
    analyze_markets,
    coinbase_doctor,
    liquidity_snapshot,
    list_markets,
    multi_timeframe_summary,
    top_movers,
    trend_signal,
    volatility_rank,
)


def _print(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def run() -> int:
    parser = argparse.ArgumentParser(description="Coinbase CLI tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("accounts")

    lm = sub.add_parser("list_markets")
    lm.add_argument("--quote", default="USD")
    lm.add_argument("--status", default=None)
    lm.add_argument("--limit", type=int, default=200)

    tm = sub.add_parser("top_movers")
    tm.add_argument("--window", default="24h")
    tm.add_argument("--quote", default="USD")
    tm.add_argument("--limit", type=int, default=10)
    tm.add_argument("--min-volume", type=float, default=0.0)

    vr = sub.add_parser("volatility_rank")
    vr.add_argument("--window", default="24h")
    vr.add_argument("--quote", default="USD")
    vr.add_argument("--limit", type=int, default=10)
    vr.add_argument("--min-candles", type=int, default=10)

    ls = sub.add_parser("liquidity_snapshot")
    ls.add_argument("--quote", default="USD")
    ls.add_argument("--limit", type=int, default=10)

    ts = sub.add_parser("trend_signal")
    ts.add_argument("product_id")
    ts.add_argument("--timeframe", default="1h")

    mts = sub.add_parser("multi_timeframe_summary")
    mts.add_argument("product_id")

    am = sub.add_parser("analyze_markets")
    am.add_argument("--quote", default="USD")
    am.add_argument("--window", default="24h")
    am.add_argument("--limit", type=int, default=20)
    am.add_argument("--min-volume", type=float, default=0.0)

    sub.add_parser("coinbase_doctor")

    amf = sub.add_parser("analyze_markets_fn")
    amf.add_argument("payload", help='JSON payload, e.g. {"quote":"USD","window":"24h","limit":20}')
    sub.add_parser("smoke")

    args = parser.parse_args()
    connector = CoinbaseConnector()
    try:
        if args.cmd == "accounts":
            output = {
                "summary": "Account endpoint requires Exchange passphrase for private REST auth; configure existing private connector for balances.",
                "data": {
                    "auth_present": bool(
                        os.environ.get("COINBASE_API_KEY")
                        and os.environ.get("COINBASE_API_SECRET")
                        and os.environ.get("COINBASE_PASSPHRASE")
                    )
                },
            }
        elif args.cmd == "list_markets":
            output = list_markets(connector, args.quote, status=args.status, limit=args.limit)
        elif args.cmd == "top_movers":
            output = top_movers(connector, args.window, args.quote, args.limit, min_volume=args.min_volume)
        elif args.cmd == "volatility_rank":
            output = volatility_rank(connector, args.window, args.quote, args.limit, min_candles=args.min_candles)
        elif args.cmd == "liquidity_snapshot":
            output = liquidity_snapshot(connector, args.quote, args.limit)
        elif args.cmd == "trend_signal":
            output = trend_signal(connector, args.product_id, args.timeframe)
        elif args.cmd == "multi_timeframe_summary":
            output = multi_timeframe_summary(connector, args.product_id)
        elif args.cmd == "analyze_markets":
            output = analyze_markets(connector, args.quote, args.window, args.limit, min_volume=args.min_volume)
        elif args.cmd == "coinbase_doctor":
            output = coinbase_doctor(connector)
        elif args.cmd == "analyze_markets_fn":
            payload = json.loads(args.payload)
            output = analyze_markets(
                connector,
                quote=payload.get("quote", "USD"),
                window=payload.get("window", "24h"),
                limit=int(payload.get("limit", 20)),
                min_volume=float(payload.get("min_volume", 0.0)),
            )
        elif args.cmd == "smoke":
            output = {
                "doctor": coinbase_doctor(connector),
                "analysis": analyze_markets(connector, quote="USD", window="24h", limit=10),
            }
        else:
            parser.error(f"unknown command: {args.cmd}")
            return 2
        _print(output)
        return 0
    except CoinbaseAPIError as exc:
        _print({"summary": "Coinbase command failed", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
