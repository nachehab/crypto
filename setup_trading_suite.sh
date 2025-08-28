#!/usr/bin/env bash
set -euo pipefail

### ─────────────────────────────────────────────────────────────────────────────
### Configurable basics
### ─────────────────────────────────────────────────────────────────────────────
WORKDIR="${HOME}/trading-bots"
RUNDIR="${WORKDIR}/run"
BINDIR="${HOME}/bin"               # runner helper scripts go here
PYENV_ROOT="${HOME}/.pyenv"

# Python versions per app
PY_FT="3.11.12"
PY_HB="3.10.17"
PY_JE="3.10.17"
PY_OB="3.10.17"
PY_CO="3.12.10"
PY_DB="3.12.10"

# Virtualenv names
VENV_FT="freqtrade-env"
VENV_HB="hummingbot-env"
VENV_JE="jesse-env"
VENV_OB="octobot-env"
VENV_CO="collector-env"
VENV_DB="dashboard-env"

### ─────────────────────────────────────────────────────────────────────────────
### Helpers
### ─────────────────────────────────────────────────────────────────────────────
log() { printf "\n\033[1;32m[✔]\033[0m %s\n" "$*"; }
warn() { printf "\n\033[1;33m[!]\033[0m %s\n" "$*"; }
note() { printf "    • %s\n" "$*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "\n\033[1;31m[✘]\033[0m Missing required command '%s'.\n" "$1" >&2
    exit 1
  fi
}

ensure_line() {
  local line file
  line="$1"; file="$2"
  grep -Fqs -- "$line" "$file" || echo "$line" >> "$file"
}

activate_pyenv_in_shells() {
  # bash
  ensure_line 'export PYENV_ROOT="$HOME/.pyenv"' "${HOME}/.bashrc"
  ensure_line 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' "${HOME}/.bashrc"
  ensure_line 'eval "$(pyenv init -)"' "${HOME}/.bashrc"
  ensure_line 'eval "$(pyenv virtualenv-init -)"' "${HOME}/.bashrc"

  # profile (login shells)
  ensure_line 'export PYENV_ROOT="$HOME/.pyenv"' "${HOME}/.profile"
  ensure_line 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' "${HOME}/.profile"
  ensure_line 'eval "$(pyenv init -)"' "${HOME}/.profile"
  ensure_line 'eval "$(pyenv virtualenv-init -)"' "${HOME}/.profile"

  # zsh, if present
  if [[ -f "${HOME}/.zshrc" ]]; then
    ensure_line 'export PYENV_ROOT="$HOME/.pyenv"' "${HOME}/.zshrc"
    ensure_line 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' "${HOME}/.zshrc"
    ensure_line 'eval "$(pyenv init -)"' "${HOME}/.zshrc"
    ensure_line 'eval "$(pyenv virtualenv-init -)"' "${HOME}/.zshrc"
  fi
}

# Non-interactive login shell (fixed)
pyenv_shell() {
  bash -lc "$*"
}

mk_runner() {
  local name="$1" body="$2"
  local path="${RUNDIR}/${name}.sh"
  mkdir -p "${RUNDIR}"
  cat > "${path}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
EOF
  printf "%s\n" "${body}" >> "${path}"
  chmod +x "${path}"
  ln -sf "${path}" "${BINDIR}/${name}"
  note "Runner created: ${path} (symlink: ${BINDIR}/${name})"
}

mk_tmux_runner() {
  local session="$1" script_path="$2"
  local wrapper="${RUNDIR}/start_${session}.sh"
  cat > "${wrapper}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
SESSION="${session}"
CMD="bash -lc '${script_path}'"
if tmux has-session -t "\$SESSION" 2>/dev/null; then
  echo "tmux session '\$SESSION' already exists."
else
  tmux new-session -d -s "\$SESSION" "\$CMD"
  echo "Started tmux session '\$SESSION'."
fi
tmux ls | grep -E "^\$SESSION:"
EOF
  chmod +x "${wrapper}"
  ln -sf "${wrapper}" "${BINDIR}/start_${session}"
  note "tmux starter: ${wrapper} (symlink: ${BINDIR}/start_${session})"
}

### ─────────────────────────────────────────────────────────────────────────────
### 1) System prerequisites
### ─────────────────────────────────────────────────────────────────────────────
log "Installing system prerequisites (build tools, SSL/DB headers, tmux, etc.)"
sudo apt-get update -y
sudo apt-get install -y \
  build-essential curl git ca-certificates tmux screen \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libffi-dev liblzma-dev tk-dev uuid-runtime \
  pkg-config

for cmd in curl git tmux screen gcc; do
  require_cmd "$cmd"
done

mkdir -p "${WORKDIR}" "${BINDIR}"

### ─────────────────────────────────────────────────────────────────────────────
### 2) pyenv + pyenv-virtualenv
### ─────────────────────────────────────────────────────────────────────────────
if [[ ! -d "${PYENV_ROOT}" ]]; then
  log "Installing pyenv"
  curl -fsSL https://pyenv.run | bash
else
  log "pyenv already installed"
fi

activate_pyenv_in_shells
export PYENV_ROOT PATH
export PYENV_ROOT="$PYENV_ROOT"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Install Python versions (idempotent)
log "Installing Python versions via pyenv (this can take a while)"
pyenv install -s "${PY_FT}"
pyenv install -s "${PY_HB}"
pyenv install -s "${PY_JE}"
pyenv install -s "${PY_OB}"
pyenv install -s "${PY_CO}"
pyenv install -s "${PY_DB}"

### ─────────────────────────────────────────────────────────────────────────────
### 3) Create virtualenvs
### ─────────────────────────────────────────────────────────────────────────────
log "Creating/updating virtualenvs"
pyenv virtualenv -f "${PY_FT}" "${VENV_FT}" || true
pyenv virtualenv -f "${PY_HB}" "${VENV_HB}" || true
pyenv virtualenv -f "${PY_JE}" "${VENV_JE}" || true
pyenv virtualenv -f "${PY_OB}" "${VENV_OB}" || true
pyenv virtualenv -f "${PY_CO}" "${VENV_CO}" || true
pyenv virtualenv -f "${PY_DB}" "${VENV_DB}" || true

### ─────────────────────────────────────────────────────────────────────────────
### 4) Freqtrade (≥3.11)
### ─────────────────────────────────────────────────────────────────────────────
log "Installing Freqtrade into ${VENV_FT}"
pyenv_shell "pyenv activate ${VENV_FT} && \
  python -m pip install --upgrade pip && \
  pip install 'git+https://github.com/freqtrade/freqtrade.git'"

FT_DIR="${WORKDIR}/freqtrade"
FT_CFG_DIR="${FT_DIR}/config/freqtrade"
FT_CFG="${FT_CFG_DIR}/config.json"
mkdir -p "${FT_CFG_DIR}"
if [[ ! -f "${FT_CFG}" ]]; then
  cat > "${FT_CFG}" <<'JSON'
{
  "dry_run": true,
  "dry_run_wallet": 10000,
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": { "enableRateLimit": true }
  },
  "pairlists": [{ "method": "StaticPairList", "pairs": ["BTC/USDT","ETH/USDT"] }],
  "timeframe": "5m",
  "strategy": "EMA_Cross"
}
JSON
  note "Created Freqtrade dry-run config at ${FT_CFG}"
fi

mk_runner "run_freqtrade" "$(cat <<'EOS'
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
EOS
)"

mk_tmux_runner "freqtrade" "${BINDIR}/run_freqtrade"

### ─────────────────────────────────────────────────────────────────────────────
### 5) Hummingbot — fixed
### ─────────────────────────────────────────────────────────────────────────────
log "Installing Hummingbot into ${VENV_HB}"
pyenv_shell "pyenv activate ${VENV_HB} && \
  python -m pip install --upgrade pip setuptools wheel && \
  pip install 'numpy==1.26.4' 'cython>=3.0,<3.2' && \
  pip install --no-build-isolation 'git+https://github.com/hummingbot/hummingbot.git'"

HB_DIR="${WORKDIR}/hummingbot"
HB_CFG_DIR="${HB_DIR}/config/hummingbot"
HB_CFG="${HB_CFG_DIR}/conf_pmm.yml"
mkdir -p "${HB_CFG_DIR}"
if [[ ! -f "${HB_CFG}" ]]; then
  cat > "${HB_CFG}" <<'YAML'
strategy: pure_market_making
exchange: binance
markets:
  - BTC-USDT
order_amount: 0.001
spreads:
  bid_spread: 0.002
  ask_spread: 0.002
dry_run: true
YAML
  note "Created Hummingbot placeholder config at ${HB_CFG}"
fi

mk_runner "run_hummingbot" "$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate hummingbot-env
HB_DIR="${HOME}/trading-bots/hummingbot"
CFG="${HB_DIR}/config/hummingbot/conf_pmm.yml"
cd "$HB_DIR"
exec hummingbot --config-file "$CFG"
EOS
)"

mk_tmux_runner "hummingbot" "${BINDIR}/run_hummingbot"

### ─────────────────────────────────────────────────────────────────────────────
### 6) Hummingbot Dashboard
### ─────────────────────────────────────────────────────────────────────────────
log "Installing Hummingbot Dashboard into ${VENV_DB}"
pyenv_shell "pyenv activate ${VENV_DB} && \
  python -m pip install --upgrade pip && \
  pip install sqlalchemy hummingbot hummingbot-api-client nest_asyncio pydantic \
    'streamlit>=1.36.0' watchdog python-dotenv 'plotly==5.24.1' pycoingecko glom defillama \
    statsmodels 'pandas_ta==0.3.14b' pyyaml pathlib streamlit-authenticator==0.3.2 \
    flake8 isort pre-commit"

DB_DIR="${WORKDIR}/dashboard"
if [[ ! -d "${DB_DIR}" ]]; then
  git clone https://github.com/hummingbot/dashboard.git "${DB_DIR}"
fi

mk_runner "run_dashboard" "$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate dashboard-env
DB_DIR="${HOME}/trading-bots/dashboard"
cd "$DB_DIR"
exec streamlit run main.py --server.headless true
EOS
)"

mk_tmux_runner "dashboard" "${BINDIR}/run_dashboard"

### ─────────────────────────────────────────────────────────────────────────────
### 7) Jesse
### ─────────────────────────────────────────────────────────────────────────────
log "Installing Jesse into ${VENV_JE}"
pyenv_shell "pyenv activate ${VENV_JE} && \
  python -m pip install --upgrade pip && \
  pip install 'git+https://github.com/jesse-ai/jesse.git'"

JE_DIR="${WORKDIR}/jesse"
JE_CFG_DIR="${JE_DIR}/config/jesse"
JE_CFG="${JE_CFG_DIR}/config.py"
mkdir -p "${JE_CFG_DIR}"
if [[ ! -f "${JE_CFG}" ]]; then
  cat > "${JE_CFG}" <<'PY'
DATA_STORAGE_PATH = "storage"
DEBUG_MODE = True
PY
  note "Created Jesse config stub at ${JE_CFG}"
fi

mk_runner "run_jesse" "$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate jesse-env
JE_DIR="${HOME}/trading-bots/jesse"
export JESSE_CONFIG_MODULE="config.jesse.config"
cd "$JE_DIR"
exec jesse run
EOS
)"

mk_tmux_runner "jesse" "${BINDIR}/run_jesse"

### ─────────────────────────────────────────────────────────────────────────────
### 8) OctoBot
### ─────────────────────────────────────────────────────────────────────────────
log "Installing OctoBot into ${VENV_OB}"
pyenv_shell "pyenv activate ${VENV_OB} && \
  python -m pip install --upgrade pip && \
  pip install 'git+https://github.com/Drakkar-Software/OctoBot.git'"

OB_DIR="${WORKDIR}/octobot"
OB_CFG_DIR="${OB_DIR}/config/octobot"
OB_CFG="${OB_CFG_DIR}/config.yaml"
mkdir -p "${OB_CFG_DIR}"
if [[ ! -f "${OB_CFG}" ]]; then
  cat > "${OB_CFG}" <<'YAML'
general:
  dry_run: true
server:
  enable_web: true
  host: 0.0.0.0
  port: 5001
YAML
  note "Created OctoBot config stub at ${OB_CFG}"
fi

mk_runner "run_octobot" "$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate octobot-env
OB_DIR="${HOME}/trading-bots/octobot"
CFG="${OB_DIR}/config/octobot/config.yaml"
cd "$OB_DIR"
exec octobot --config "$CFG"
EOS
)"

mk_tmux_runner "octobot" "${BINDIR}/run_octobot"

### ─────────────────────────────────────────────────────────────────────────────
### 9) Collector
### ─────────────────────────────────────────────────────────────────────────────
log "Setting up Collector into ${VENV_CO}"
pyenv_shell "pyenv activate ${VENV_CO} && \
  python -m pip install --upgrade pip"

CO_DIR="${WORKDIR}/collector"
mkdir -p "${CO_DIR}/collector"
CO_REQ="${CO_DIR}/collector/requirements.txt"
CO_SCRIPT="${CO_DIR}/collector/normalize_trades.py"

if [[ -f "${CO_REQ}" ]]; then
  pyenv_shell "pyenv activate ${VENV_CO} && pip install -r '${CO_REQ}'"
fi

if [[ ! -f "${CO_SCRIPT}" ]]; then
  cat > "${CO_SCRIPT}" <<'PY'
#!/usr/bin/env python
import time, sys
print("Collector normalize_trades.py placeholder running. Press Ctrl+C to stop.")
try:
    while True:
        print("Normalizing trades... (placeholder)"); sys.stdout.flush()
        time.sleep(10)
except KeyboardInterrupt:
    print("Exiting.")
PY
  chmod +x "${CO_SCRIPT}"
  note "Created Collector script placeholder at ${CO_SCRIPT}"
fi

mk_runner "run_collector" "$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate collector-env
CO_DIR="${HOME}/trading-bots/collector"
SCRIPT="${CO_DIR}/collector/normalize_trades.py"
cd "$CO_DIR"
exec python "$SCRIPT" "$@"
EOS
)"

mk_tmux_runner "collector" "${BINDIR}/run_collector"

### ─────────────────────────────────────────────────────────────────────────────
### 10) Final notes
### ─────────────────────────────────────────────────────────────────────────────
log "All set! Runners and tmux starters created."
cat <<'INFO'

Usage examples:
  start_freqtrade
  start_hummingbot
  start_dashboard
  start_jesse
  start_octobot
  start_collector

To attach:  tmux attach -t freqtrade   (replace with session name)

INFO
