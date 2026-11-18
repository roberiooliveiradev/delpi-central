#!/usr/bin/env python3
"""ATLAS HML producer packaging-review entrypoint — NOT INSTALLABLE."""
from __future__ import annotations

from linux_ops_mcp.atlas_hml_b_runtime_packaging import run_packaging_entrypoint

if __name__ == "__main__":
    raise SystemExit(run_packaging_entrypoint("producer"))
