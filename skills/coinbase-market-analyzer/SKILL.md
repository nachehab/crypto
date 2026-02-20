---
name: coinbase-market-analyzer
description: Coinbase Exchange market scanner and technical analysis tools for liquid SYMBOL-USD pairs.
version: 1.2.0
tags: ["coinbase","exchange","markets","analysis","trading"]
metadata: {"runtime":"python3","entrypoint":"{baseDir}/scripts/coinbase_cli.py","tooling":"wrapper-shell","openclaw":{"requires":{"bins":["python3"],"env":["COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PASSPHRASE"]},"primaryEnv":{"apiKey":"COINBASE_API_KEY"}}}
---

# Coinbase Market Analyzer Skill

## Env injection (OpenClaw)

Configure env through `skills.entries.coinbase-market-analyzer.env` (preferred) or `skills.entries.coinbase-market-analyzer.apiKey`.

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
python3 {baseDir}/scripts/coinbase_cli.py coinbase_doctor
python3 {baseDir}/scripts/coinbase_cli.py list_markets --quote USD --status online --limit 50
python3 {baseDir}/scripts/coinbase_cli.py top_movers --window 24h --quote USD --limit 20 --min-volume 1000000
python3 {baseDir}/scripts/coinbase_cli.py volatility_rank --window 4h --quote USD --limit 20 --min-candles 12
python3 {baseDir}/scripts/coinbase_cli.py liquidity_snapshot --quote USD --limit 20
python3 {baseDir}/scripts/coinbase_cli.py trend_signal BTC-USD --timeframe 1h
python3 {baseDir}/scripts/coinbase_cli.py multi_timeframe_summary BTC-USD
python3 {baseDir}/scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 20 --min-volume 1000000
python3 {baseDir}/scripts/coinbase_cli.py smoke
```

## Agent-callable wrappers

Use wrapper scripts inside the skill folder:

- `{baseDir}/bin/coinbase_doctor.sh`
- `{baseDir}/bin/coinbase_list_markets.sh`
- `{baseDir}/bin/coinbase_top_movers.sh`
- `{baseDir}/bin/coinbase_volatility_rank.sh`
- `{baseDir}/bin/coinbase_liquidity_snapshot.sh`
- `{baseDir}/bin/coinbase_trend_signal.sh`
- `{baseDir}/bin/coinbase_multi_timeframe_summary.sh`
- `{baseDir}/bin/coinbase_analyze_markets.sh`
- `{baseDir}/bin/coinbase_analyze_markets_fn.sh`

Legacy wrappers remain at `agents/main/agent/bin/*.sh` for backward compatibility and redirect to `{baseDir}/bin`.

## Chat examples

- `analyze_markets({"quote":"USD","window":"24h","limit":20,"min_volume":1000000})`
- `top_movers({"window":"4h","quote_currency":"USD","limit":15,"min_volume":500000})`
- `trend_signal({"product_id":"SOL-USD","timeframe":"1h"})`

## Troubleshooting

- Auth failures: run `{baseDir}/bin/coinbase_doctor.sh`; add missing env keys to `skills.entries.coinbase-market-analyzer.env`.
- Missing env in chat: verify wrappers source `{baseDir}/bin/openclaw_env.sh`.
- `command not found`: use `{baseDir}/bin/*` wrappers instead of bare command names in tool wiring.
- Rate limit responses: built-in retries obey `Retry-After` and exponential backoff with jitter.
