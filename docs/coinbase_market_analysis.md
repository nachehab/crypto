# Coinbase Market Analysis Extension

## New CLI functions

All commands return structured JSON with `summary` and `data`.

```bash
python3 scripts/coinbase_cli.py coinbase_doctor
python3 scripts/coinbase_cli.py list_markets --quote USD --status online --limit 50
python3 scripts/coinbase_cli.py top_movers --window 24h --quote USD --limit 20 --min-volume 1000000
python3 scripts/coinbase_cli.py volatility_rank --window 24h --quote USD --limit 20 --min-candles 12
python3 scripts/coinbase_cli.py liquidity_snapshot --quote USD --limit 20
python3 scripts/coinbase_cli.py trend_signal BTC-USD --timeframe 1h
python3 scripts/coinbase_cli.py multi_timeframe_summary BTC-USD
python3 scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 20 --min-volume 1000000
python3 scripts/coinbase_cli.py analyze_markets_fn '{"quote":"USD","window":"24h","limit":20,"min_volume":1000000}'
python3 scripts/coinbase_cli.py smoke
```

## Agent-callable wrappers

Use wrapper scripts under `agents/main/agent/bin` so runtime env vars from `openclaw.json` are injected before execution:

```bash
agents/main/agent/bin/coinbase_doctor.sh
agents/main/agent/bin/coinbase_list_markets.sh --quote USD --status online --limit 50
agents/main/agent/bin/coinbase_top_movers.sh --window 24h --quote USD --limit 20 --min-volume 1000000
agents/main/agent/bin/coinbase_volatility_rank.sh --window 24h --quote USD --limit 20 --min-candles 12
agents/main/agent/bin/coinbase_liquidity_snapshot.sh --quote USD --limit 20
agents/main/agent/bin/coinbase_trend_signal.sh BTC-USD --timeframe 1h
agents/main/agent/bin/coinbase_multi_timeframe_summary.sh BTC-USD
agents/main/agent/bin/coinbase_analyze_markets.sh --quote USD --window 24h --limit 20 --min-volume 1000000
agents/main/agent/bin/coinbase_analyze_markets_fn.sh '{"quote":"USD","window":"24h","limit":20,"min_volume":1000000}'
agents/main/agent/bin/coinbase_accounts.sh
```

## Runtime/env behavior

- `agents/main/agent/bin/openclaw_env.sh` reads `openclaw.json` (`env.vars`) and exports entries for tool execution.
- `openclaw.json` contains `skills.entries.coinbase-market-analyzer.env` placeholders for OpenClaw-native env injection.
- This fixes chat-tool runs where shell state is missing `COINBASE_API_KEY`/`COINBASE_API_SECRET`/`COINBASE_PASSPHRASE`.

## Exchange API alignment

- Public analysis uses Exchange market-data endpoints (`/products`, `/ticker`, `/stats`, `/candles`, `/book`).
- Pagination helper supports cursor-style `cb-after` traversal for list endpoints.
- Retry policy handles transient errors and rate limits with `Retry-After` + exponential backoff + jitter.
- Private auth checks in `coinbase_doctor` use Exchange HMAC headers when full creds are provided.

## Smoke test

```bash
bash scripts/coinbase_smoke_test.sh
```

## Troubleshooting

- Auth failures: run `coinbase_doctor`; ensure env keys are set in `skills.entries.coinbase-market-analyzer.env`.
- Missing env in agent runs: verify `openclaw_env.sh` is sourced by wrapper scripts.
- `command not found`: wire tools to absolute wrapper paths under `agents/main/agent/bin`.
- Rate limit responses: allow automatic retries; avoid tight loops in external callers.
