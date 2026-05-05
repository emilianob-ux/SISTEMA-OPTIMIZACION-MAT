#!/usr/bin/env python3
"""Wrapper: anade la raiz del repo a sys.path y ejecuta el CLI."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.binance_vision.cli import main

if __name__ == "__main__":
    main()
