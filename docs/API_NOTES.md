# Coinbase Exchange API Notes

## Base URL

- Default: `https://api.exchange.coinbase.com`

## Endpoints used

- `GET /time` for connectivity check in `coinbase_doctor()`.
- `GET /accounts` for optional authenticated validation in `coinbase_doctor()` when credentials are present.
- `GET /products` for market listing and symbol metadata.
- `GET /products/{product_id}/ticker` for latest trade price.
- `GET /products/{product_id}/stats` for 24h change/volume baseline.
- `GET /products/{product_id}/candles` for volatility and trend calculations.
- `GET /products/{product_id}/book?level=2` for liquidity and spread estimation.

## Auth

Exchange REST signing headers:

- `CB-ACCESS-KEY`
- `CB-ACCESS-SIGN`
- `CB-ACCESS-TIMESTAMP`
- `CB-ACCESS-PASSPHRASE`

Signature format: `base64(hmac_sha256(base64_decode(secret), timestamp + method + path + body))`.

## Rate limits and retries

- Handles `429` and `5xx` with bounded exponential backoff and jitter.
- Retry default: up to 4 attempts.
- `Retry-After` header is respected when provided.

## Pagination

- Generic cursor pagination helper supports `before`/`after` style query and `CB-BEFORE`/`CB-AFTER` response headers.
- Current tool paths primarily use non-paginated market endpoints, but helper is available for paginated Exchange resources.
