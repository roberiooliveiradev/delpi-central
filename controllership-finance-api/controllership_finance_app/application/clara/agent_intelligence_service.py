"""CLARA agent intelligence — persona projection for the MCP adapter.

``agent_directives`` rides on ``get_catalog`` →
``capability_surface.agent_directives`` so the host receives the compact
character context (CHARACTER-PROFILE-CLARA-001) alongside the operational
directives. Fiction only: the projected ``character`` never authorizes a
tool, permission or operation — backend AuthZ remains authoritative.
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

from controllership_finance_app.persona.clara_profile import (
    get_clara_profile,
)

CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "clara_agent_intelligence.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_clara_agent_intelligence_cache() -> None:
    _load.cache_clear()


class ClaraAgentIntelligenceService:
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
            "citations": (
                "Conhecimento retornado traz citation_locator e "
                "evidence_classification — apresente ambos."
            ),
            "confirmation": (
                "Toda ACT exige proposal_handle de PREPARE + "
                "confirmação humana explícita da operação exata."
            ),
            "character": cls.persona_context(),
        }

    @classmethod
    def character_profile(cls) -> CharacterProfile:
        """Canonical CLARA ficha (shared contract consumer)."""
        return get_clara_profile()

    @classmethod
    def persona_context(cls) -> dict[str, Any]:
        """Compact narrative context from the ficha — MCP/agent echo."""
        return project_persona_context(cls.character_profile())

    @classmethod
    def public_profile(cls) -> CharacterPublicProfile:
        """Approved public narrative projection for colleague knowledge."""
        return project_public_profile(cls.character_profile())
