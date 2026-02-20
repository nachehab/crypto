# OpenClaw Coinbase Exchange Workspace

Minimal OpenClaw workspace for Coinbase Advanced Trade market discovery and analysis.

## Quickstart

1. Configure environment variables:
   - `COINBASE_API_KEY`
   - `COINBASE_API_SECRET`
   - optional `COINBASE_API_URL` (defaults to `https://api.exchange.coinbase.com`)
2. Advanced Trade mode: `COINBASE_API_KEY` + `COINBASE_API_SECRET` are used for authenticated checks.
3. Confirm `openclaw.json` loads workspace skills and maps `skills.entries.coinbase-exchange.env`.
4. Run tests:
   - `python -m unittest discover -s skills/coinbase-exchange/tests -p 'test_*.py'`
5. Run smoke test:
   - `python skills/coinbase-exchange/scripts/smoke_test.py`

See `docs/SETUP.md` and `docs/API_NOTES.md` for details.
