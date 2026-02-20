#!/usr/bin/env bash
set -euo pipefail
python3 "$(cd "$(dirname "$0")" && pwd)/coinbase_cli.py" coinbase_doctor
python3 "$(cd "$(dirname "$0")" && pwd)/coinbase_cli.py" analyze_markets --quote USD --window 24h --limit 10
