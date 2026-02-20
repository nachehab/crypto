#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path

REAL = Path(__file__).resolve().parents[1] / "skills" / "coinbase-market-analyzer" / "scripts" / "coinbase_cli.py"
runpy.run_path(str(REAL), run_name="__main__")
