# TOOLS.md

## Tool Execution Defaults
- Use real tool calls for all data retrieval and actions.
- Never simulate tool output when tools are available.
- Keep responses concise and numeric for trading outputs.

## Market Data Defaults (Intraday Swing)
- Primary timeframes: 1H and 4H.
- Candle request size: 200 bars for each timeframe.
- Always fetch current price and 24h stats (change %, volume).
- Optional depth context: order book snapshot when available.

## Trading/Risk Defaults
- Max exposure default: 5% of available capital.
- Stop/invalidation baseline: ATR14 from 1H timeframe.
- Analysis/prediction does not imply execution.
- Execution requires explicit user trade command and pre-trade balance check.

## Symbol Handling
- Accept generic symbols using `SYMBOL-USD` format.
- Keep backward compatibility with XRP-first account display where configured.
