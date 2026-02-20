# Coinbase Market Analysis Extension

## Primary skill paths

All Coinbase analyzer runtime assets now live under `skills/coinbase-market-analyzer/`.

```bash
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py coinbase_doctor
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py list_markets --quote USD --status online --limit 50
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py top_movers --window 24h --quote USD --limit 20 --min-volume 1000000
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py volatility_rank --window 24h --quote USD --limit 20 --min-candles 12
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py liquidity_snapshot --quote USD --limit 20
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py trend_signal BTC-USD --timeframe 1h
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py multi_timeframe_summary BTC-USD
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 20 --min-volume 1000000
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py analyze_markets_fn '{"quote":"USD","window":"24h","limit":20,"min_volume":1000000}'
python3 skills/coinbase-market-analyzer/scripts/coinbase_cli.py smoke
```

## Agent-callable wrappers

Preferred wrapper path:

```bash
skills/coinbase-market-analyzer/bin/coinbase_doctor.sh
skills/coinbase-market-analyzer/bin/coinbase_list_markets.sh --quote USD --status online --limit 50
skills/coinbase-market-analyzer/bin/coinbase_top_movers.sh --window 24h --quote USD --limit 20 --min-volume 1000000
skills/coinbase-market-analyzer/bin/coinbase_volatility_rank.sh --window 24h --quote USD --limit 20 --min-candles 12
skills/coinbase-market-analyzer/bin/coinbase_liquidity_snapshot.sh --quote USD --limit 20
skills/coinbase-market-analyzer/bin/coinbase_trend_signal.sh BTC-USD --timeframe 1h
skills/coinbase-market-analyzer/bin/coinbase_multi_timeframe_summary.sh BTC-USD
skills/coinbase-market-analyzer/bin/coinbase_analyze_markets.sh --quote USD --window 24h --limit 20 --min-volume 1000000
skills/coinbase-market-analyzer/bin/coinbase_analyze_markets_fn.sh '{"quote":"USD","window":"24h","limit":20,"min_volume":1000000}'
skills/coinbase-market-analyzer/bin/coinbase_accounts.sh
```

Backward-compatible shims remain at `agents/main/agent/bin/*.sh` and `scripts/coinbase_*.py`.

## Runtime/env behavior

- Env is injected from `openclaw.json` via `skills.entries.coinbase-market-analyzer.env`.
- `skills.entries.coinbase-market-analyzer.apiKey` maps to `COINBASE_API_KEY` fallback.
- Wrapper bootstrap script: `skills/coinbase-market-analyzer/bin/openclaw_env.sh`.

## Smoke test

```bash
bash skills/coinbase-market-analyzer/scripts/coinbase_smoke_test.sh
```
