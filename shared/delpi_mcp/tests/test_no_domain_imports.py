"""Static guard: delpi_mcp must never import domain/app namespaces.

Lightweight text scan — enough to stop accidental coupling; AST tooling is
unnecessary for an import whitelist this small.
"""

from __future__ import annotations

import re
from pathlib import Path

import delpi_mcp

_FORBIDDEN = re.compile(
    r"^\s*(?:from|import)\s+(tv_app|tm_app|app\.|app\b(?!_)|delpi_domain)\b",
    re.MULTILINE,
)


def test_delpi_mcp_has_no_domain_imports():
    pkg_dir = Path(delpi_mcp.__file__).parent
    offenders = []
    for py in pkg_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for m in _FORBIDDEN.finditer(text):
            offenders.append(f"{py.name}: {m.group(0).strip()}")
    assert offenders == []


def test_delpi_mcp_has_no_top_level_mcp_sdk_dependency():
    """SDK imports must stay lazy (function-level) — the package must remain
    importable without the mcp SDK installed."""
    pkg_dir = Path(delpi_mcp.__file__).parent
    mcp_import = re.compile(r"^(?:from|import)\s+mcp\b", re.MULTILINE)
    offenders = [
        py.name
        for py in pkg_dir.glob("*.py")  # package modules only, not tests
        if mcp_import.search(py.read_text(encoding="utf-8"))
    ]
    assert offenders == []
