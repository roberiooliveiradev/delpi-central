"""Static guards: the contract stays pure — no domain, SDK, network, auth
or filled-profile data inside the shared package."""

from __future__ import annotations

import re
from pathlib import Path

import delpi_character_profiles

_PKG_DIR = Path(delpi_character_profiles.__file__).parent

_FORBIDDEN_IMPORTS = re.compile(
    r"^\s*(?:from|import)\s+(tv_app|tm_app|app\.|app\b(?!_)|delpi_domain|"
    r"mcp|openai|starlette|flask|fastapi|requests|httpx|urllib|socket|"
    r"keycloak|jose|delpi_auth|delpi_mcp)\b",
    re.MULTILINE,
)


def test_no_forbidden_imports() -> None:
    offenders = []
    for py in _PKG_DIR.rglob("*.py"):
        if "tests" in py.parts:
            continue
        for m in _FORBIDDEN_IMPORTS.finditer(py.read_text("utf-8")):
            offenders.append(f"{py.name}: {m.group(0).strip()}")
    assert offenders == []


def test_no_prefilled_specialist_profiles() -> None:
    """Shared must not ship DAVI/VISTA/TÉO/EVA/CLARA fichas — each MCP owns
    its own. Only the relationship-vocabulary constants may mention real
    names nowhere."""
    for py in _PKG_DIR.rglob("*.py"):
        if "tests" in py.parts:
            continue  # tests use generic ALPHA/BETA fixtures
        text = py.read_text("utf-8")
        for name in ('"davi"', '"vista"', '"teo"', '"eva"', '"clara"',
                     "character_id=\"davi\"", "character_id=\"vista\""):
            assert name not in text.lower(), f"{py.name} ships '{name}'"


def test_import_has_no_side_effects() -> None:
    """Importing in a clean interpreter must not pull third-party modules."""
    import subprocess
    import sys

    code = (
        "import sys;"
        "import delpi_character_profiles;"
        "bad=[m for m in sys.modules if not m.startswith(('delpi_character_profiles','_')) "
        "and m.split('.')[0] not in "
        "{m.split('.')[0] for m in list(sys.stdlib_module_names)}];"
        "print(bad);"
        "sys.exit(1 if bad else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=_PKG_DIR.parent,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_filled_profile_files() -> None:
    """No JSON/YAML profile artifacts inside the package — fichas are local
    to each MCP."""
    artifacts = [
        p for p in _PKG_DIR.rglob("*")
        if p.suffix in {".json", ".yaml", ".yml", ".toml"}
    ]
    assert artifacts == []
