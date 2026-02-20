# Setup

## 1) Environment variables

Set variables in the environment used by OpenClaw runtime:

- `COINBASE_API_KEY`
- `COINBASE_API_SECRET`
- `COINBASE_PASSPHRASE`
- `COINBASE_API_URL` (optional)

The workspace does not depend on interactive shell exports; values are injected by `skills.entries.coinbase-exchange.env` in `openclaw.json`.

## 2) openclaw.json validation

Required structure:

- `skills.load.workspace: true`
- `skills.entries.coinbase-exchange.enabled: true`
- `skills.entries.coinbase-exchange.env` includes all Coinbase credential variables.
- `skills.entries.coinbase-exchange.apiKey` is mapped.

## 3) Run checks

```bash
python -m unittest discover -s skills/coinbase-exchange/tests -p 'test_*.py'
python skills/coinbase-exchange/scripts/smoke_test.py
```

## Troubleshooting

- **Env var not found**: run `coinbase_doctor()` and confirm `checks` output for each required variable.
- **401/403**: verify key/secret/passphrase match Coinbase Exchange credentials and key permissions.
- **429**: lower `limit` in tool calls; client retries with exponential backoff and jitter.
- **Command not found**: use `python` explicitly when running test commands.
