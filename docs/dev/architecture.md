# Developer Architecture Notes

## Coinbase analyzer organization

- Canonical implementation: `skills/coinbase-market-analyzer/scripts/`.
- Compatibility shims:
  - `scripts/coinbase_cli.py`
  - `scripts/coinbase_analysis.py`
  - `scripts/coinbase_smoke_test.sh`
  - `agents/main/agent/bin/coinbase_*.sh`

These shims preserve existing CLI/tool call sites while keeping the skill self-contained.
