# HEARTBEAT.md

## Optional Monitoring Tasks
- Track configured watchlist symbols on 1H and 4H cadence.
- Alert when any tracked symbol moves more than 3% within 1H.
- Alert when 1H EMA20/EMA50 crossover occurs.
- Alert when 4H regime flips (HH/HL -> LH/LL, or inverse).
- Alert when 24h volume spikes above configured multiple of rolling average.

## Alert Payload (Concise)
- Symbol
- Trigger condition
- Current price
- 1H change %
- 24h volume
- Suggested next action: `analyze <symbol>`

## Safety
- Heartbeat alerts are informational only.
- No automatic trade placement from heartbeat conditions.
