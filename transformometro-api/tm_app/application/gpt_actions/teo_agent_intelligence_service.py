"""Deployable TÉO agent intelligence (not GPT Builder Instructions).

Loaded from ``teo_agent_intelligence.json`` and projected on
``gpt_get_catalog`` / MCP ``get_catalog`` → ``capability_surface.agent_directives``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "teo_agent_intelligence.json"
)

_LIST_CAP_KEYS = frozenset({"examples", "examplePrompts", "anti_patterns", "forbidden", "when", "rules"})
_MAX_LIST_ITEMS = 12
_MAX_ANTI_PATTERNS = 32
_DROP_DIRECTIVE_KEYS = frozenset({"summary", "example", "examples", "examplePrompts"})


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_teo_agent_intelligence_cache() -> None:
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


class TeoAgentIntelligenceService:
    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def version(cls) -> str:
        return str(cls.document().get("version") or "").strip()

    @classmethod
    def agent_directives(cls, transport: str = "gpt_actions") -> dict[str, Any]:
        """Compact directives for the external specialist to obey at runtime.

        ``transport="gpt_actions"`` (default) preserves the Actions contract:
        ``gpt_*`` names, additive ``commit_now`` write-flow and the canonical
        ``surface_parity.parity_map``. ``transport="mcp"`` projects the same
        document for MCP consumers: ``write_flow_mcp`` replaces the Actions
        write-flow, ``*_actions`` sections are dropped, and every ``gpt_*``
        name is rewritten through the canonical parity map — zero
        ``commit_now`` / atomic prepare+commit semantics.
        """
        from tm_app.application.intelligence.capability_registry import (
            actions_parity,
            actions_to_mcp_primary,
        )
        from tm_app.application.intelligence.transport_projection import (
            neutralize_for_mcp,
        )

        doc = cls.document()
        posture = dict(doc.get("execution_posture") or {})
        rules_actions = posture.pop("rules_actions", []) or []
        forbidden_actions = posture.pop("forbidden_actions", []) or []
        anti_patterns = list(doc.get("anti_patterns") or [])
        parity = dict(doc.get("surface_parity") or {})
        if transport == "mcp":
            authority = (
                "Obey these directives from live get_catalog. "
                "They override stale catalog knowledge for mutation behavior."
            )
        else:
            authority = (
                "Obey these directives from live gpt_get_catalog / get_catalog. "
                "They override stale Builder Knowledge for mutation behavior."
            )
            posture["rules"] = list(posture.get("rules") or []) + list(rules_actions)
            posture["forbidden"] = (
                list(posture.get("forbidden") or []) + list(forbidden_actions)
            )
            anti_patterns += list(doc.get("anti_patterns_actions") or [])
            # Canonical parity record: gpt operationId → MCP tool names.
            parity["parity_map"] = {
                gpt_op: list(tools) for gpt_op, tools in actions_parity().items()
            }
            parity["parity_map_primary"] = actions_to_mcp_primary()
        raw = {
            "version": cls.version(),
            "authority": authority,
            "actions_runtime": doc.get("actions_runtime") or {},
            "execution_posture": posture,
            "write_flow": doc.get("write_flow") or {},
            "write_flow_mcp": doc.get("write_flow_mcp") or {},
            "multi_action": doc.get("multi_action") or {},
            "product_guide": doc.get("product_guide") or {},
            "modes": doc.get("modes") or {},
            "epistemology": doc.get("epistemology") or {},
            "discovery": doc.get("discovery") or {},
            "language": doc.get("language") or {},
            "surface_parity": parity,
            "anti_patterns": anti_patterns,
            "auth_errors": doc.get("auth_errors") or {},
            "not_exposed": doc.get("not_exposed") or {},
            "flows": doc.get("flows") or {},
        }
        if transport == "mcp":
            raw.pop("write_flow", None)
            raw = neutralize_for_mcp(raw)
        else:
            raw.pop("write_flow_mcp", None)
        return _compact_for_actions(raw)
