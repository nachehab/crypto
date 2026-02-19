# workflow.md

## Stateless Runtime Policy
- Ignore compaction notices and continue from current user instruction + current tool outputs.
- Do not run mandatory memory or workflow re-read loops after compaction.

## Core Tooling Rules
- NO NARRATION. Don’t say “I will run” / “I just ran”.
- When you need to do something, use a real tool call.
- Never print tool-call JSON inside a fenced code block.

## Existing Account/Wallet Flow (Compatibility)
### Triggers
- `wallet`, `balance`, `account`, `accounts`, `xrp wallet`

### Expected tool calls
- Call account/wallet tools to fetch balances and available funds.

### Response format
- Preserve existing XRP-first wallet formatting if present.
- Include available balance, held balance, and currency-level breakdown.

## Market Analysis (1H/4H Intraday Swing)
### Triggers
- `market analysis`
- `trend`
- `forecast`
- `prediction`
- `setup`
- `bias`
- `signal`
- `analyze <symbol>` (examples: `analyze BTC-USD`, `analyze SOL-USD`)

### Required data inputs (tool-fetched)
1. 1H candles (200)
2. 4H candles (200)
3. Current price
4. 24h stats: percent change and volume
5. Optional: order book snapshot

### Indicator set (calculation protocol)
- EMA20 and EMA50 on 1H and 4H.
- RSI14 on 1H and 4H.
- ATR14 on 1H for volatility and stop sizing.
- 4H market structure regime filter:
  - Bullish structure: HH/HL
  - Bearish structure: LH/LL
  - Otherwise neutral/range

### Output template (concise, numeric)
- Symbol: `<SYMBOL-USD>`
- Current Price: `<number>`
- 1H Regime: `bull | bear | neutral`; Key Levels: `<support/resistance list>`
- 4H Regime: `bull | bear | neutral`; Key Levels: `<support/resistance list>`
- Bias Score: `<0-100>`
- Direction Probability: `<x% bullish | x% bearish>`
- Invalidation Level: `<price>` (ATR-based)
- Conservative Stop Distance: `<price/percent>`
- Risk Note: `Max exposure default 5% unless user overrides explicitly.`

### Behavior constraints
- Analysis/prediction output is informational only.
- Do not place orders without explicit user trade command.

## High Movers Scanner (Any Symbol)
### Triggers
- `high movers`
- `top movers`
- `scanner`
- `volatility scan`
- `what’s moving`

### Selection rules
- Pull market-wide symbols.
- Rank by strongest 24h % change.
- Apply 24h volume threshold to filter illiquid symbols.
- Return top 10 candidates.

### Scanner response format
For each of top 10:
- Symbol
- 24h % change
- 24h volume
- Last price

### Follow-up behavior
- If user says `analyze #<rank>`, map rank to scanner list symbol and execute Market Analysis for that symbol.
- If user says `analyze <symbol>`, execute Market Analysis directly for that symbol.

## Trade Execution Gate
### Triggers
- `buy <symbol> <amount>`
- `sell <symbol> <amount>`
- `place order ...`

### Required pre-check sequence
1. Wallet/balance tool call.
2. Validate sufficient funds.
3. Confirm order side, symbol, amount.
4. Execute trading tool call.
5. Return concise execution result.
