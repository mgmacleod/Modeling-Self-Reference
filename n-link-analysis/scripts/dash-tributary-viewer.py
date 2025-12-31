#!/usr/bin/env python3
"""Compatibility shim.

The basin geometry Dash app moved to:
  n-link-analysis/viz/dash-basin-geometry-viewer.py

This file remains so older notes/commands keep working.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> int:
    target = Path(__file__).resolve().parents[1] / "viz" / "dash-basin-geometry-viewer.py"
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
