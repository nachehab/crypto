#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
config_path="${OPENCLAW_CONFIG_PATH:-$repo_root/openclaw.json}"
skill_name="${OPENCLAW_SKILL_NAME:-coinbase-market-analyzer}"

if [[ -f "$config_path" ]]; then
  eval "$(python3 - "$config_path" "$skill_name" <<'PY'
import json, os, re, shlex, sys
path, skill_name = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as fh:
    cfg = json.load(fh)

exports = {}
for k, v in (cfg.get('env', {}).get('vars', {}) or {}).items():
    if isinstance(v, str):
        exports[k] = v

entry = (cfg.get('skills', {}).get('entries', {}) or {}).get(skill_name, {})
for k, v in (entry.get('env', {}) or {}).items():
    if isinstance(v, str):
        exports[k] = v

api_key = entry.get('apiKey')
if isinstance(api_key, str) and api_key:
    exports.setdefault('COINBASE_API_KEY', api_key)

pattern = re.compile(r'^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$')
for k, v in list(exports.items()):
    m = pattern.match(v)
    if m:
        exports[k] = os.environ.get(m.group(1), v)

for k, v in exports.items():
    print(f"export {k}={shlex.quote(v)}")
PY
)"
fi
