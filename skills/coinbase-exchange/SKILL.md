---
name: coinbase-exchange
description: Coinbase Exchange market tools (markets, movers, volatility, liquidity, signals)
metadata: {"openclaw":{"requires":{"env":["COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PASSPHRASE"],"bins":[],"config":["skills.entries.coinbase-exchange"]}}}
---

Use Python modules under `{baseDir}/src`.

## Tools

- `coinbase_doctor()`
- `list_markets({"quote_currency":"USD","status":"online","limit":50})`
- `top_movers({"window":"24h","quote_currency":"USD","limit":20,"min_volume":1000000})`
- `volatility_rank({"window":"4h","quote_currency":"USD","limit":20,"min_candles":24})`
- `liquidity_snapshot({"quote_currency":"USD","limit":20})`
- `trend_signal({"product_id":"BTC-USD","timeframe":"4h"})`
- `analyze_markets({"quote_currency":"USD","window":"24h","limit":20,"min_volume":1000000})`

## Implementation references

- Client: `{baseDir}/src/client.py`
- Markets: `{baseDir}/src/markets.py`
- Analytics: `{baseDir}/src/analytics.py`
- Tool wrappers: `{baseDir}/src/tools.py`
- Schemas: `{baseDir}/src/schema.py`

## Smoke test

`python {baseDir}/scripts/smoke_test.py`
