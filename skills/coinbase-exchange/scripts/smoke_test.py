import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

import tools  # noqa: E402


def main() -> None:
    doctor = tools.coinbase_doctor()
    payload = {"doctor": doctor}
    try:
        analysis = tools.analyze_markets({"quote_currency": "USD", "window": "24h", "limit": 5})
        payload["analysis_summary"] = analysis.get("summary")
        payload["count"] = len(analysis.get("items", []))
    except Exception as exc:  # noqa: BLE001
        payload["analysis_error"] = str(exc)
        payload["count"] = 0
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
