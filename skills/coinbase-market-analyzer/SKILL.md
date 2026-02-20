---
name: coinbase-market-analyzer
version: 1.0.0
description: Coinbase Exchange market analysis with top movers, volatility ranking, liquidity snapshots, and multi-timeframe trend signals
author: OpenClaw Codex
capabilities: ["market_data", "technical_analysis", "trading_signals"]
env: {"COINBASE_API_KEY": "required", "COINBASE_API_SECRET": "required"}
commands: {"analyze_markets": "Comprehensive market analysis pipeline", "list_markets": "List available trading pairs", "top_movers": "Rank markets by price change", "volatility_rank": "Rank by realized volatility", "liquidity_snapshot": "Spread and depth analysis", "trend_signal": "RSI/EMA/ATR trend indicators", "multi_timeframe_summary": "Combined 1h/4h/1d analysis", "coinbase_doctor": "Diagnostics and connectivity check"}
---

# Coinbase Market Analyzer

## Overview
Analyzes Coinbase Exchange markets using official CDP Exchange REST API. Provides agent-callable tools for market discovery, volatility analysis, liquidity assessment, and multi-timeframe technical signals.

## Authentication
Requires Coinbase CDP API credentials configured in OpenClaw:
- `COINBASE_API_KEY`: Your organization/project API key
- `COINBASE_API_SECRET`: EC private key (PEM format)

Set in `openclaw.json`:
```json
{
  "skills": {
    "entries": {
      "coinbase-market-analyzer": {
        "enabled": true,
        "env": {
          "COINBASE_API_KEY": "${COINBASE_API_KEY}",
          "COINBASE_API_SECRET": "${COINBASE_API_SECRET}"
        }
      }
    }
  }
}
```

## Available Functions

### `coinbase_doctor()`
Validates configuration, authentication, and connectivity.
Returns diagnostic report with actionable next steps.

### `list_markets(options)`
Lists available trading pairs with metadata.
- `quote_currency` (optional): Filter by quote currency (USD, CAD, etc.)
- `status` (optional): Filter by status (online, offline)
- `limit` (optional): Max results

### `top_movers(options)`
Ranks markets by 24h price change.
- `window`: Time window ("1h", "4h", "24h")
- `quote_currency`: Quote currency filter
- `limit`: Number of results
- `min_volume` (optional): Minimum 24h volume filter

### `volatility_rank(options)`
Ranks markets by realized volatility from candle data.
- `window`: Time window
- `quote_currency`: Quote currency filter
- `limit`: Number of results
- `min_candles` (optional): Minimum data quality threshold

### `liquidity_snapshot(options)`
Analyzes spread and top-of-book depth.
- `quote_currency`: Quote currency filter
- `limit`: Number of results

### `trend_signal(options)`
Computes RSI14, EMA slope, ATR for single product.
- `product_id`: Product identifier (e.g., "BTC-USD")
- `timeframe`: Candle timeframe ("1h", "4h", "1d")
Returns: RSI, EMA20, EMA50, ATR14, trend_label (bullish/neutral/bearish)

### `multi_timeframe_summary(options)`
Combines 1h/4h/1d analysis with conflict detection.
- `product_id`: Product identifier
Returns: Signals across timeframes + unified verdict

### `analyze_markets(options)`
**Main orchestrator** - combines all analysis functions.
- `quote_currency`: "USD" (default)
- `window`: "24h" (default)
- `limit`: 20 (default)
- `min_volume` (optional): Volume filter

Returns ranked list with schema:
```json
{
  "product_id": "BTC-USD",
  "base": "BTC",
  "quote": "USD",
  "price": 95420.50,
  "change_pct": 3.2,
  "volume": 1250000000,
  "volatility": 0.045,
  "spread": 0.01,
  "trend_label": "bullish",
  "notes": ["High volume", "Strong uptrend"],
  "reasons": ["Top 3 mover", "Low spread", "Bullish 4H trend"]
}
```

## Agent Usage Examples

```
You: What are the top movers today?
Agent: [calls top_movers(window="24h", quote_currency="USD", limit=10)]

You: Analyze BTC market structure
Agent: [calls multi_timeframe_summary(product_id="BTC-USD")]

You: Scan for high volatility opportunities
Agent: [calls analyze_markets(quote_currency="USD", window="24h", limit=20)]

You: Check if Coinbase connection is working
Agent: [calls coinbase_doctor()]
```

## CLI Usage

```bash
# Run from workspace root
node skills/coinbase-market-analyzer/dist/index.js analyze_markets --quote USD --limit 10

# Or via OpenClaw native command
claw skill run coinbase-market-analyzer analyze_markets --quote=USD
```

## Troubleshooting

### "Command not found" or tool not available
- Ensure skill is enabled in `openclaw.json`: `skills.entries.coinbase-market-analyzer.enabled = true`
- Rebuild skill: `cd skills/coinbase-market-analyzer && pnpm install && pnpm build`
- Restart OpenClaw gateway

### Authentication failures (401/403)
- Run `coinbase_doctor()` for diagnostics
- Verify `COINBASE_API_KEY` and `COINBASE_API_SECRET` are set in OpenClaw config
- Check key format: API key should be `organizations/{uuid}/apiKeys/{uuid}`
- Secret should be PEM-formatted EC private key with escaped newlines

### Rate limit errors (429)
- Implementation includes exponential backoff with jitter
- Reduce concurrent requests or add delays between calls
- Coinbase Exchange public endpoints: ~10 req/sec, authenticated: varies by tier

### Missing candle data
- Some markets lack historical data on newer pairs
- Functions fallback to ticker/stats when candles unavailable
- Check `min_candles` parameter in volatility_rank

## Technical Notes

- **Pagination**: Automatically handles paginated responses (cursor-based and page-based)
- **Rate Limiting**: Implements exponential backoff (2^attempt * 1000ms + jitter)
- **Retries**: 3 attempts for transient failures (network errors, 5xx responses)
- **Caching**: No internal caching; designed for real-time data
- **Dependencies**: Minimal - uses Node.js crypto module for request signing

## References
- CDP Exchange API Docs: https://docs.cdp.coinbase.com/exchange/introduction/welcome
- REST API Reference: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/introduction
- OpenClaw Skills Spec: https://docs.openclaw.ai/tools/skills
