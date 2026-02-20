# WORKFLOW_AUTO.md

## Auto Workflow Runtime Rules
- Ignore compaction notices.
- Continue from current instruction + live tool outputs only.
- Do not require post-compaction audits or forced re-reading of workflow/memory files.

## Core Protocol Rules
- NO NARRATION. Don’t say “I will run” / “I just ran”.
- When you need to do something, use a real tool call.
- Never print tool-call JSON inside a fenced code block.

## Auto Trigger Map

### 1) Wallet / Account Queries
**Triggers**: `wallet`, `balance`, `account`, `accounts`, `xrp wallet`

**Action**:
- Run wallet/account tool calls.
- Keep XRP-first output compatibility when applicable.
- Also support generic symbol balances.

### 2) Market Analysis (1H/4H)
**Triggers**:
- `market analysis`, `trend`, `forecast`, `prediction`, `setup`, `bias`, `signal`
- `analyze <symbol>`

**Required tool data**:
- 1H candles (200)
- 4H candles (200)
- Current price
- 24h % change + 24h volume
- Optional order book snapshot

**Compute protocol**:
- EMA20/EMA50 on 1H and 4H
- RSI14 on 1H and 4H
- ATR14 on 1H for stop/invalidation sizing
- 4H structure filter (HH/HL bullish, LH/LL bearish, else neutral)

**Output schema**:
- Symbol
- Current price
- 1H regime + key levels
- 4H regime + key levels
- Bias score (0–100)
- Direction probability (e.g., `62% bullish`)
- ATR-based invalidation level
- Conservative stop distance
- Risk note: max exposure default 5% unless explicitly overridden

**Safety**:
- Never execute trades from analysis/prediction trigger alone.

### 3) High Movers Scanner
**Triggers**: `high movers`, `top movers`, `scanner`, `volatility scan`, `what’s moving`

**Action**:
- Fetch broad market symbols and 24h stats.
- Filter by minimum 24h volume threshold.
- Rank by absolute/positive 24h % movers per strategy.
- Return top 10 with:
  - symbol
  - 24h % change
  - 24h volume
  - last price

**Follow-up**:
- `analyze #3` -> analyze symbol at rank 3.
- `analyze <symbol>` -> analyze explicit symbol.

### 4) Trade Execution
**Triggers**: `buy <symbol> <amount>`, `sell <symbol> <amount>`, `place order ...`

**Required sequence**:
1. Wallet/balance check via tool call.
2. Validate funds and order fields.
3. Place order via execution tool.
4. Return concise execution status.

**Risk control**:
- Default max exposure 5% unless explicit user override.

## Coinbase Market Analysis Tool Calls

- `coinbase_doctor` -> run `agents/main/agent/bin/coinbase_doctor.sh`
- `analyze_markets({quote, window, limit})` -> run `agents/main/agent/bin/coinbase_analyze_markets.sh --quote <quote> --window <window> --limit <limit>`
- Additional direct tools:
  - `list_markets`
  - `top_movers`
  - `volatility_rank`
  - `liquidity_snapshot`
  - `trend_signal`
  - `multi_timeframe_summary`

All functions must return JSON with `summary` and `data`.
