import base64
import hashlib
import hmac
import json
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CoinbaseExchangeError(Exception):
    pass


class CoinbaseExchangeClient:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 15, max_retries: int = 4) -> None:
        self.base_url = (base_url or os.getenv("COINBASE_API_URL") or "https://api.exchange.coinbase.com").rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = os.getenv("COINBASE_API_KEY", "")
        self.api_secret = os.getenv("COINBASE_API_SECRET", "")

    def _auth_headers(self, method: str, path: str, body: str) -> Dict[str, str]:
        timestamp = str(time.time())
        secret = self.api_secret
        try:
            decoded_secret = base64.b64decode(secret)
        except Exception as exc:  # noqa: BLE001
            raise CoinbaseExchangeError("COINBASE_API_SECRET must be base64 encoded") from exc
        prehash = f"{timestamp}{method.upper()}{path}{body}"
        signature = base64.b64encode(hmac.new(decoded_secret, prehash.encode("utf-8"), hashlib.sha256).digest()).decode("utf-8")
        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
        }

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        auth: bool = False,
    ) -> Tuple[Any, Dict[str, str]]:
        query = f"?{urlencode(params)}" if params else ""
        req_path = f"{path}{query}"
        url = f"{self.base_url}{req_path}"
        body = json.dumps(data) if data else ""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "openclaw-coinbase-exchange-skill/1.0",
        }
        if auth:
            headers.update(self._auth_headers(method, path, body))

        for attempt in range(self.max_retries + 1):
            request = Request(url=url, method=method.upper(), headers=headers, data=body.encode("utf-8") if body else None)
            try:
                with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                    raw = response.read().decode("utf-8")
                    payload = json.loads(raw) if raw else {}
                    response_headers = {k: v for k, v in response.headers.items()}
                    return payload, response_headers
            except HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                if status in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    sleep_s = float(retry_after) if retry_after else min(8.0, (2**attempt) + random.random())
                    time.sleep(sleep_s)
                    continue
                detail = raw[:400] if raw else str(exc)
                raise CoinbaseExchangeError(f"HTTP {status} for {path}: {detail}") from exc
            except URLError as exc:
                if attempt < self.max_retries:
                    time.sleep(min(5.0, (2**attempt) + random.random()))
                    continue
                raise CoinbaseExchangeError(f"Network error for {path}: {exc}") from exc
        raise CoinbaseExchangeError(f"Exceeded retries for {path}")

    def paginate(self, path: str, params: Optional[Dict[str, Any]] = None, cursor: str = "after", limit_pages: int = 10) -> List[Any]:
        all_items: List[Any] = []
        local_params = dict(params or {})
        for _ in range(limit_pages):
            payload, headers = self.request("GET", path, params=local_params)
            if isinstance(payload, list):
                all_items.extend(payload)
            else:
                all_items.append(payload)
            next_cursor = headers.get("CB-AFTER") if cursor == "after" else headers.get("CB-BEFORE")
            if not next_cursor:
                break
            local_params[cursor] = next_cursor
        return all_items
