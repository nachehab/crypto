from typing import Any, Dict, List


REQUIRED_MARKET_KEYS = ["product_id", "base", "quote", "status"]


def validate_market(item: Dict[str, Any]) -> Dict[str, Any]:
    missing = [k for k in REQUIRED_MARKET_KEYS if k not in item or item[k] in (None, "")]
    if missing:
        raise ValueError(f"missing market keys: {', '.join(missing)}")
    return item


def normalize_market(product: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "product_id": product.get("id"),
        "base": product.get("base_currency"),
        "quote": product.get("quote_currency"),
        "status": product.get("status", "unknown"),
        "min_size": product.get("base_min_size"),
        "quote_increment": product.get("quote_increment"),
        "base_increment": product.get("base_increment"),
    }
    return validate_market(normalized)


def result(ok: bool, summary: str, **kwargs: Any) -> Dict[str, Any]:
    payload = {"ok": ok, "summary": summary}
    payload.update(kwargs)
    return payload


def ensure_list(items: Any) -> List[Any]:
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    return items
