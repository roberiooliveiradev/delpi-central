"""Coleta operation_id usados nos routers envelope (exceto NC)."""

from __future__ import annotations

import re
from pathlib import Path

import app.interface.http.openapi_agent_metadata as agent_metadata

ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app/interface/http/routes"
SKIP_FILES = frozenset({"internal_nc_routes.py", "external_nc_routes.py"})

_LITERAL_PATTERN = re.compile(r"""operation_id\s*=\s*["']([^"']+)["']""")
_CONST_PATTERN = re.compile(
    r"""operation_id\s*=\s*([A-Z][A-Z0-9_]*)\[["']operation_id["']\]"""
)

_DYNAMIC_OPERATION_IDS = frozenset(
    {
        "get_ppm_internal_series",
        "get_ppm_external_series",
    }
)


def collect_operation_ids_from_routes() -> set[str]:
    ids: set[str] = set()

    for path in ROUTES_ROOT.rglob("*.py"):
        if path.name in SKIP_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        ids.update(_LITERAL_PATTERN.findall(text))

        for const_name in _CONST_PATTERN.findall(text):
            const = getattr(agent_metadata, const_name, None)
            if isinstance(const, dict):
                operation_id = const.get("operation_id")
                if isinstance(operation_id, str) and operation_id:
                    ids.add(operation_id)

    ids.update(_DYNAMIC_OPERATION_IDS)
    return ids
