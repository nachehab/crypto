---
name: coinbase-market-analyzer
description: Coinbase Exchange market scanner and technical analysis tools for liquid SYMBOL-USD pairs.
version: 1.1.0
tags: ["coinbase","exchange","markets","analysis","trading"]
metadata: {"runtime":"python3","entrypoint":"scripts/coinbase_cli.py","tooling":"wrapper-shell"}
---

# Coinbase Market Analyzer Skill

## Env injection (OpenClaw)

Configure env through OpenClaw `skills.entries.coinbase-market-analyzer.env` (preferred) or `skills.entries.coinbase-market-analyzer.apiKey`.

```json
{
  "skills": {
    "entries": {
      "coinbase-market-analyzer": {
        "enabled": true,
        "env": {
          "COINBASE_API_KEY": "${COINBASE_API_KEY}",
          "COINBASE_API_SECRET": "${COINBASE_API_SECRET}",
          "COINBASE_PASSPHRASE": "${COINBASE_PASSPHRASE}"
        },
        "apiKey": "${COINBASE_API_KEY}"
      }
    }
  }
}
```

Public market-data endpoints do not require auth. Exchange private REST checks (`/accounts`) require API key + secret + passphrase.

## CLI usage

```bash
python3 scripts/coinbase_cli.py coinbase_doctor
python3 scripts/coinbase_cli.py list_markets --quote USD --status online --limit 50
python3 scripts/coinbase_cli.py top_movers --window 24h --quote USD --limit 20 --min-volume 1000000
python3 scripts/coinbase_cli.py volatility_rank --window 4h --quote USD --limit 20 --min-candles 12
python3 scripts/coinbase_cli.py liquidity_snapshot --quote USD --limit 20
python3 scripts/coinbase_cli.py trend_signal BTC-USD --timeframe 1h
python3 scripts/coinbase_cli.py multi_timeframe_summary BTC-USD
python3 scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 20 --min-volume 1000000
python3 scripts/coinbase_cli.py smoke
```

## Agent-callable wrappers

Use absolute-path wrappers under `agents/main/agent/bin`:

- `coinbase_doctor.sh`
- `coinbase_list_markets.sh`
- `coinbase_top_movers.sh`
- `coinbase_volatility_rank.sh`
- `coinbase_liquidity_snapshot.sh`
- `coinbase_trend_signal.sh`
- `coinbase_multi_timeframe_summary.sh`
- `coinbase_analyze_markets.sh`
- `coinbase_analyze_markets_fn.sh`

## Chat examples

- `analyze_markets({"quote":"USD","window":"24h","limit":20,"min_volume":1000000})`
- `top_movers({"window":"4h","quote_currency":"USD","limit":15,"min_volume":500000})`
- `trend_signal({"product_id":"SOL-USD","timeframe":"1h"})`

## Troubleshooting

- Auth failures: run `coinbase_doctor`; add missing env keys to `skills.entries.coinbase-market-analyzer.env`.
- Missing env in chat: verify wrapper scripts source `agents/main/agent/bin/openclaw_env.sh`.
- `command not found`: use wrappers instead of bare `python` command names in tool wiring.
- Rate limit responses: built-in retries obey `Retry-After` and exponential backoff with jitter.
