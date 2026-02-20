# Skills Index

## coinbase-market-analyzer

- **Name:** `coinbase-market-analyzer`
- **Description:** Coinbase Exchange market scanner and technical analysis tools for liquid `SYMBOL-USD` pairs.
- **Location:** `skills/coinbase-market-analyzer`
- **Required bins:** `python3`
- **Required env vars:** `COINBASE_API_KEY`, `COINBASE_API_SECRET`, `COINBASE_PASSPHRASE`
- **Primary env/api key mapping:** `primaryEnv.apiKey -> COINBASE_API_KEY`
- **What it does:**
  - Coinbase Exchange market listing and filtering
  - top movers + volatility ranking
  - liquidity snapshot
  - trend and multi-timeframe summaries (1H/4H-oriented)
  - doctor/smoke checks for auth and runtime readiness
