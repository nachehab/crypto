# Migration Log

## Skill/runtime file moves

- `scripts/coinbase_analysis.py` -> `skills/coinbase-market-analyzer/scripts/coinbase_analysis.py`
- `scripts/coinbase_cli.py` -> `skills/coinbase-market-analyzer/scripts/coinbase_cli.py`
- `scripts/coinbase_smoke_test.sh` -> `skills/coinbase-market-analyzer/scripts/coinbase_smoke_test.sh`

## Documentation moves

- `WORKFLOW_AUTO.md` -> `docs/openclaw/workflow_auto.md`
- `workflow.md` -> `docs/openclaw/workflow.md`
- `HEARTBEAT.md` -> `docs/openclaw/heartbeat.md`
- `TOOLS.md` -> `docs/openclaw/tools.md`
- `docs/coinbase_market_analysis.md` -> `docs/coinbase/market_analysis.md`

## Added/renamed files

- Added `docs/openclaw/skills_loading.md`
- Added `docs/dev/architecture.md`
- Added `docs/SKILLS_INDEX.md`
- Added `docs/MIGRATION_LOG.md`

## Compatibility wrappers/shims

- Added script shims at original paths:
  - `scripts/coinbase_cli.py`
  - `scripts/coinbase_analysis.py`
  - `scripts/coinbase_smoke_test.sh`
- Added canonical skill wrappers:
  - `skills/coinbase-market-analyzer/bin/*.sh`
- Updated legacy wrapper path behavior by redirecting:
  - `agents/main/agent/bin/coinbase_*.sh` -> `skills/coinbase-market-analyzer/bin/*.sh`
  - `agents/main/agent/bin/openclaw_env.sh` -> `skills/coinbase-market-analyzer/bin/openclaw_env.sh`

## Notes

- `AGENTS.md` intentionally remains in repo root to preserve instruction scope.
- No duplicate workspace skill names were introduced.
