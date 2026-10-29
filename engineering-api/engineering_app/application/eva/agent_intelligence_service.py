"""EVA agent intelligence — persona projection for the MCP adapter.

``agent_directives`` rides on ``get_catalog`` → ``data.agent_directives``
so the host receives the compact character context
(EVA-CHARACTER-PROFILE-001) alongside the operational directives.
Fiction only: the projected ``character`` never authorizes a tool,
permission or operation — backend AuthZ remains authoritative.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from delpi_character_profiles import (
    CharacterProfile,
    CharacterPublicProfile,
    project_persona_context,
    project_public_profile,
)

from engineering_app.persona.eva_profile import get_eva_profile

CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "eva_agent_intelligence.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_eva_agent_intelligence_cache() -> None:
    _load.cache_clear()


class EvaAgentIntelligenceService:
    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def version(cls) -> str:
        return str(cls.document().get("version") or "").strip()

    @classmethod
    def agent_directives(cls) -> dict[str, Any]:
        """Directives projected on ``get_catalog`` for the MCP transport.

        Operational directives preserved verbatim; ``character`` is the
        compact narrative projection from the shared-contract ficha —
        fiction only, never AuthZ/capability/tool authority.
        """
        return {
            "read_first": (
                "Responda estado operacional somente com resultado "
                "de tool READ — nunca de memória."
            ),
            "provenance": (
                "Dados oficiais vêm da Engineering API — distinga "
                "observações, inferências e fatos oficiais e "
                "preserve a proveniência das fontes."
            ),
            "boundaries": (
                "EVA é somente leitura: não recalcula indicadores, "
                "não inventa valores e não executa ACT — qualquer "
                "write segue contratos governados com confirmação "
                "humana e autorização efetiva do backend."
            ),
            "character": cls.persona_context(),
        }

    @classmethod
    def character_profile(cls) -> CharacterProfile:
        """Canonical EVA ficha (shared contract consumer)."""
        return get_eva_profile()

    @classmethod
    def persona_context(cls) -> dict[str, Any]:
        """Compact narrative context from the ficha — MCP/agent echo."""
        return project_persona_context(cls.character_profile())

    @classmethod
    def public_profile(cls) -> CharacterPublicProfile:
        """Approved public narrative projection for colleague knowledge."""
        return project_public_profile(cls.character_profile())
