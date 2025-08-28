#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate octobot-env
OB_DIR="$HOME/trading-bots/octobot"
CFG="$OB_DIR/config/octobot/config.yaml"
cd "$OB_DIR"
python -c "import OctoBot" 2>/dev/null && exec python -m OctoBot --config "$CFG"
exec python -m octobot --config "$CFG"
