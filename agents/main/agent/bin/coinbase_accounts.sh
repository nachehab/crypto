#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../../../.." && pwd)"

CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-${ROOT_DIR}/openclaw.json}"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-}"

if [[ -z "${WORKSPACE_DIR}" && -f "${CONFIG_PATH}" ]]; then
  WORKSPACE_DIR="$(python3 - <<'PY' "${CONFIG_PATH}"
import json,sys
p=sys.argv[1]
try:
    with open(p) as f:
        c=json.load(f)
    print(c.get('agents',{}).get('defaults',{}).get('workspace',''))
except Exception:
    print('')
PY
)"
fi

CANDIDATES=(
  "${WORKSPACE_DIR}/skills/coinbase-advanced-trader/scripts/coinbase_cli.py"
  "${ROOT_DIR}/skills/coinbase-advanced-trader/scripts/coinbase_cli.py"
)

for candidate in "${CANDIDATES[@]}"; do
  if [[ -n "${candidate}" && -f "${candidate}" ]]; then
    exec python3 "${candidate}" accounts
  fi
done

echo "coinbase_accounts: could not find coinbase_cli.py in expected skill paths" >&2
echo "checked:" >&2
for candidate in "${CANDIDATES[@]}"; do
  [[ -n "${candidate}" ]] && echo "  - ${candidate}" >&2
done
exit 1
