"""EVA agent intelligence — persona projection for the MCP adapter.

``agent_directives`` rides on ``get_catalog`` → ``data.agent_directives``
so the host receives the compact character context
(EVA-CHARACTER-PROFILE-001) alongside the operational directives.
Fiction only: the projected ``character`` never authorizes a tool,
permission or operation — backend AuthZ remains authoritative.
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from delpi_character_profiles import (
    CharacterProfile,
    CharacterPublicProfile,
    project_persona_context,
    project_public_profile,
)

from engineering_app.config import settings
from engineering_app.persona.eva_profile import get_eva_profile

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_PUBLIC_ORIGIN_FALLBACK = "https://minhadelpi.com.br"


@lru_cache(maxsize=8)
def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

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
                "EVA não recalcula indicadores e não inventa valores. "
                "Escrita segue contratos governados da Engineering "
                "API: PREPARE/dry-run primeiro, confirmação humana "
                "explícita (confirmed=true), AuthZ Core live, "
                "postcondition por read-back — o ambiente pode "
                "bloquear ACT e a recusa é respondida honestamente."
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
        base = (os.getenv("PUBLIC_BASE_URL") or _PUBLIC_ORIGIN_FALLBACK).rstrip("/")
        root = settings.ENGINEERING_API_ROOT_PATH.rstrip("/")
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
