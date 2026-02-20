from typing import Any, Dict, List, Optional

from client import CoinbaseExchangeClient
from schema import normalize_market


def list_markets(
    client: CoinbaseExchangeClient,
    quote_currency: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    products, _ = client.request("GET", "/products")
    normalized: List[Dict[str, Any]] = []
    for product in products:
        market = normalize_market(product)
        if quote_currency and market["quote"] != quote_currency:
            continue
        if status and market["status"] != status:
            continue
        normalized.append(market)
        if len(normalized) >= limit:
            break
    return normalized
