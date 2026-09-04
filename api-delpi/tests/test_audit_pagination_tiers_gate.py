"""Smoke: audit_pagination_tiers gate stays green."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _API_ROOT / "scripts" / "audit_pagination_tiers.py"


def test_audit_pagination_tiers_check_complete() -> None:
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--check-complete"],
        cwd=_API_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
