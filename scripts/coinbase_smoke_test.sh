#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
bash "$repo_root/skills/coinbase-market-analyzer/scripts/coinbase_smoke_test.sh" "$@"
