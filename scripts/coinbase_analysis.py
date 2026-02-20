#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parents[1] / "skills" / "coinbase-market-analyzer" / "scripts" / "coinbase_analysis.py"
_SPEC = importlib.util.spec_from_file_location(__name__, _REAL)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load Coinbase analysis module from {_REAL}")
_MOD = importlib.util.module_from_spec(_SPEC)
sys.modules[__name__] = _MOD
_SPEC.loader.exec_module(_MOD)
