#!/usr/bin/env bash
set -euo pipefail
python3 scripts/coinbase_cli.py coinbase_doctor
python3 scripts/coinbase_cli.py analyze_markets --quote USD --window 24h --limit 10
