"""Deployable TÉO agent intelligence (not GPT Builder Instructions).

Loaded from ``teo_agent_intelligence.json`` and projected on
``gpt_get_catalog`` / MCP ``get_catalog`` → ``capability_surface.agent_directives``.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from delpi_character_profiles import (
    CharacterProfile,
    CharacterPublicProfile,
    project_persona_context,
    project_public_profile,
)

from tm_app.config import settings

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_PUBLIC_ORIGIN_FALLBACK = "https://minhadelpi.com.br"


@lru_cache(maxsize=8)
def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    from tm_app.persona.teo_profile import get_teo_profile

    get_teo_profile.cache_clear()


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
            "identity": doc.get("identity") or {},
            "actions_runtime": doc.get("actions_runtime") or {},
            "execution_posture": posture,
            "write_flow": doc.get("write_flow") or {},
            "write_flow_mcp": doc.get("write_flow_mcp") or {},
            "multi_action": doc.get("multi_action") or {},
            "product_guide": doc.get("product_guide") or {},
            "solutions": doc.get("solutions") or {},
            "knowledge_orchestration": doc.get("knowledge_orchestration") or {},
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
        out = _compact_for_actions(raw)
        # CHARACTER-PROFILE-TEO-001 — compact character context projected
        # from the shared-contract ficha (single narrative source; fiction
        # only, never AuthZ/capability/tool authority). Appended after the
        # directive compactor: project_persona_context is already bounded
        # by contract and the compactor would strip *_summary keys.
        out["character"] = cls.persona_context()
        return out

    @classmethod
    def character_profile(cls) -> CharacterProfile:
        """Canonical TÉO ficha (shared contract consumer)."""
        from tm_app.persona.teo_profile import get_teo_profile

        return get_teo_profile()

    @classmethod
    def persona_context(cls) -> dict[str, Any]:
        """Compact narrative context from the ficha — MCP/Actions echo."""
        context = project_persona_context(cls.character_profile())
        distribution = cls.avatar_distribution()
        if distribution:
            context["avatar_distribution"] = distribution
        return context

    @classmethod
    def avatar_distribution(cls) -> dict[str, Any] | None:
        """Public HTTPS discovery metadata for the official avatar.

        DELPI-CHARACTER-AVATARS-002 — owner-local additive key on the
        persona projection (no shared-contract change). The URL composes
        ``PUBLIC_BASE_URL`` + service root path + the canonical
        ``avatar_reference`` filename — never user input. ``sha256`` is
        computed from the served asset so projection and route cannot
        drift. ``None`` when the ficha has no approved avatar (safe
        fail: no URL is published for unapproved or missing assets).
        """
        profile = cls.character_profile()
        appearance = profile.appearance
        reference = (appearance.avatar_reference or "").strip()
        if appearance.avatar_status != "OFFICIAL_AVATAR_APPROVED" or not reference:
            return None
        path = (_SERVICE_ROOT / reference).resolve()
        if not path.is_file() or not path.is_relative_to(_SERVICE_ROOT):
            return None
        filename = PurePosixPath(reference).name
        base = (settings.PUBLIC_BASE_URL or _PUBLIC_ORIGIN_FALLBACK).rstrip("/")
        root = settings.TM_API_ROOT_PATH.rstrip("/")
        return {
            "kind": "public_https",
            "url": (
                f"{base}{root}/public/characters/"
                f"{profile.identity.character_id}/avatar/{filename}"
            ),
            "version": Path(filename).stem,
            "mime_type": _MIME_BY_SUFFIX.get(
                path.suffix.lower(), "application/octet-stream"
            ),
            "sha256": _file_sha256(path),
        }

    @classmethod
    def public_profile(cls) -> CharacterPublicProfile:
        """Approved public narrative projection for colleague knowledge."""
        return project_public_profile(cls.character_profile())
