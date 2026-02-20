#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/openclaw_env.sh"
python3 "$script_dir/../scripts/coinbase_cli.py" top_movers "$@"
