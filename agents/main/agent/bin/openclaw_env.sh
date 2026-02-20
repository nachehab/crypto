#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
config_path="${OPENCLAW_CONFIG_PATH:-$repo_root/openclaw.json}"

if [[ -f "$config_path" ]]; then
  eval "$(python3 - "$config_path" <<'PY'
import json, shlex, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fh:
    cfg = json.load(fh)
for k, v in (cfg.get('env', {}).get('vars', {}) or {}).items():
    if isinstance(v, str):
        print(f"export {k}={shlex.quote(v)}")
PY
)"
fi

export PATH="$repo_root/scripts:$PATH"
