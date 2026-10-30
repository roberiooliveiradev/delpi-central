"""CAIO agent service — persona projection and MCP directives.

Mirrors the EVA pattern (``EvaAgentIntelligenceService``) at the
Commercial owner: operational directives plus a compact narrative
projection of the local ficha — fiction only, never AuthZ, capability
or tool authority.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any

from delpi_character_profiles import (
    CharacterProfile,
    project_persona_context,
)

from commercial_app.config import settings
from commercial_app.persona.caio_profile import get_caio_profile

_PUBLIC_ORIGIN_FALLBACK = "https://minhadelpi.com.br"

_SERVICE_ROOT = Path(__file__).resolve().parents[3]


class CaioAgentService:
    """Owner-local CAIO persona/directive projection for the MCP."""

    @classmethod
    def agent_directives(cls) -> dict[str, Any]:
        """Directives projected on ``get_context`` — operational rules
        verbatim; ``character`` is the compact narrative projection."""
        return {
            "read_first": (
                "Responda estado operacional somente com resultado de "
                "tool READ — nunca de memória."
            ),
            "provenance": (
                "Dados oficiais vêm da commercial-api — distinga "
                "observações, inferências e fatos oficiais e preserve "
                "a proveniência das fontes."
            ),
            "boundaries": (
                "CAIO não recalcula indicadores e não inventa valores. "
                "Escritas e exclusões comerciais exigem contrato "
                "governado ativado pelo owner — operações não "
                "disponíveis respondem not_implemented honestamente."
            ),
            "character": cls.persona_context(),
        }

    @classmethod
    def character_profile(cls) -> CharacterProfile:
        """Canonical CAIO ficha (shared contract consumer)."""
        return get_caio_profile()

    @classmethod
    def persona_context(cls) -> dict[str, Any]:
        """Compact narrative context from the ficha — MCP/agent echo."""
        context = project_persona_context(cls.character_profile())
        distribution = cls.avatar_distribution()
        if distribution:
            context["avatar_distribution"] = distribution
        return context

    @classmethod
    def avatar_distribution(cls) -> dict[str, Any] | None:
        """Public HTTPS discovery metadata for the official avatar.

        DELPI-CHARACTER-AVATARS-002 pattern — owner-local additive key.
        ``None`` when the ficha has no approved avatar (PENDING_ASSET):
        no URL is published for unapproved or missing assets.
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
        base = (os.getenv("PUBLIC_BASE_URL") or _PUBLIC_ORIGIN_FALLBACK).rstrip("/")
        root = settings.COMMERCIAL_API_ROOT_PATH.rstrip("/")
        return {
            "url": (
                f"{base}{root}/public/characters/"
                f"{profile.identity.character_id}/avatar/{filename}"
            ),
            "filename": filename,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "media_type": "image/jpeg",
            "distribution": "public",
        }
