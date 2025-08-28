#!/usr/bin/env bash
set -euo pipefail
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate freqtrade-env
FT_DIR="${HOME}/trading-bots/freqtrade"
CFG="${FT_DIR}/config/freqtrade/config.json"
cd "$FT_DIR"
exec freqtrade trade --dry-run --config "$CFG" --strategy EMA_Cross --api-server
