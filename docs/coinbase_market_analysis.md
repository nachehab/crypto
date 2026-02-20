# Coinbase Market Analysis Extension

## New CLI functions

All commands return structured JSON with `summary` and `data`.

```bash
python3 scripts/coinbase_cli.py coinbase_doctor
python3 scripts/coinbase_cli.py list_markets --quote USD
python3 scripts/coinbase_cli.py top_movers --window 24h --quote USD --limit 20
python3 scripts/coinbase_cli.py volatility_rank --window 24h --quote USD --limit 20
python3 scripts/coinbase_cli.py liquidity_snapshot --quote USD --limit 20
python3 scripts/coinbase_cli.py trend_signal BTC-USD --timeframe 1h
python3 scripts/coinbase_cli.py multi_timeframe_summary BTC-USD
python3 scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 20
python3 scripts/coinbase_cli.py analyze_markets_fn '{"quote":"USD","window":"24h","limit":20}'
python3 scripts/coinbase_cli.py smoke
```

## Agent-callable wrappers

Use wrapper scripts under `agents/main/agent/bin` so runtime env vars from `openclaw.json` are injected before execution:

```bash
agents/main/agent/bin/coinbase_doctor.sh
agents/main/agent/bin/coinbase_analyze_markets.sh --quote USD --window 24h --limit 20
agents/main/agent/bin/coinbase_analyze_markets_fn.sh '{"quote":"USD","window":"24h","limit":20}'
agents/main/agent/bin/coinbase_accounts.sh
```

For chat/tool wiring, call `coinbase_analyze_markets.sh` with:

```json
{"quote":"USD","window":"24h","limit":20}
```

This maps to `analyze_markets({quote:"USD", window:"24h", limit:20})` and returns ranked markets with machine-parseable fields:

- `product_id`
- `base`
- `quote`
- `price`
- `change_pct`
- `volume`
- `volatility`
- `spread`
- `trend_label`
- `notes`

## Runtime/env behavior

`agents/main/agent/bin/openclaw_env.sh` reads `openclaw.json` (`env.vars`) and exports entries for tool execution.

This fixes command runs where chat-tool shells miss `COINBASE_API_KEY` / `COINBASE_API_SECRET`.

## Error handling

- API failures return JSON error payloads and non-zero exit code.
- `coinbase_doctor` reports auth mode, lightweight endpoint status, and permission-check limitations.
- Empty/partial market data is handled by skipping failing products and preserving successful results.
