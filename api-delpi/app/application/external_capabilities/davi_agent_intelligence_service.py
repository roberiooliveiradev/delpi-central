"""Deployable DAVI agent intelligence (not Agent Studio / MCP paste).

Loaded from ``davi_agent_intelligence.json`` and projected on
``gpt_get_catalog`` / ``discover_delpi_information`` →
``capability_surface.agent_directives``.

READ-only: no write_flow / commit_now.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "davi_agent_intelligence.json"
)

# Soft budget for projected directives (E0: OpenAPI GPT ~5KiB; execute 64KiB).
# Directives ride on catalog/discover — keep well under 16KiB serialized.
DAVI_AGENT_DIRECTIVES_MAX_BYTES = 16 * 1024

_LIST_CAP_KEYS = frozenset(
    {"examples", "examplePrompts", "anti_patterns", "forbidden", "when", "rules"}
)
_MAX_LIST_ITEMS = 12
_MAX_ANTI_PATTERNS = 32
_DROP_DIRECTIVE_KEYS = frozenset({"summary", "example", "examples", "examplePrompts"})


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_davi_agent_intelligence_cache() -> None:
    _load.cache_clear()


def _compact_for_actions(node: Any, *, key: str | None = None) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for child_key, value in node.items():
            if child_key in _DROP_DIRECTIVE_KEYS:
                continue
            out[str(child_key)] = _compact_for_actions(value, key=str(child_key))
        return out
    if isinstance(node, list):
        if key == "anti_patterns":
            trimmed = node[:_MAX_ANTI_PATTERNS]
        elif key in _LIST_CAP_KEYS:
            trimmed = node[:_MAX_LIST_ITEMS]
        else:
            trimmed = node
        return [_compact_for_actions(item, key=key) for item in trimmed]
    return node


class DaviAgentIntelligenceService:
    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def version(cls) -> str:
        return str(cls.document().get("version") or "").strip()

    @classmethod
    def agent_directives(cls) -> dict[str, Any]:
        doc = cls.document()
        raw = {
            "version": cls.version(),
            "read_only": True,
            "authority": (
                "Obey these directives from live gpt_get_catalog / "
                "discover_delpi_information.capability_surface. "
                "They override stale Agent Studio / MCP paste for operational "
                "READ behavior. Persona/identity stay in stable Instructions."
            ),
            "actions_runtime": doc.get("actions_runtime") or {},
            "discovery": doc.get("discovery") or {},
            "execution_posture": doc.get("execution_posture") or {},
            "modes": doc.get("modes") or {},
            "language": doc.get("language") or {},
            "persona_bridge": doc.get("persona_bridge") or {},
            "surface_parity": doc.get("surface_parity") or {},
            "anti_patterns": list(doc.get("anti_patterns") or []),
            "auth_errors": doc.get("auth_errors") or {},
            "not_exposed": doc.get("not_exposed") or {},
            "flows": doc.get("flows") or {},
        }
        # Hard deny write-oriented keys if ever present in content.
        raw.pop("write_flow", None)
        raw.pop("commit_now", None)
        return _compact_for_actions(raw)

    @classmethod
    def capability_surface(cls) -> dict[str, Any]:
        return {"agent_directives": cls.agent_directives()}

    @classmethod
    def directives_serialized_size(cls) -> int:
        return len(
            json.dumps(cls.agent_directives(), ensure_ascii=False).encode("utf-8")
        )
