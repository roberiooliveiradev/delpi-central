"""Deployable VISTA agent intelligence (not GPT Builder Instructions).

Loaded from ``vista_agent_intelligence.json`` and projected on
``gpt_get_catalog`` → ``capability_surface.agent_directives`` so behavior
evolves with API deploy without re-pasting Builder Instructions.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "vista_agent_intelligence.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_vista_agent_intelligence_cache() -> None:
    _load.cache_clear()


class VistaAgentIntelligenceService:
    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def version(cls) -> str:
        return str(cls.document().get("version") or "").strip()

    @classmethod
    def agent_directives(cls) -> dict[str, Any]:
        """Compact directives for the external specialist to obey at runtime."""
        from tv_app.application.services.data.presentation_recipe_service import (
            PresentationRecipeService,
        )

        doc = cls.document()
        recipes = doc.get("presentation_recipes") or {}
        if isinstance(recipes, dict) and not recipes.get("catalog"):
            # Live catalog of recipe ids/markers from content JSON.
            recipes = {
                **recipes,
                "catalog": PresentationRecipeService.catalog_projection(),
            }
        return {
            "version": cls.version(),
            "authority": (
                "Obey these directives from live gpt_get_catalog. "
                "They override stale Builder Knowledge for mutation behavior."
            ),
            "execution_posture": doc.get("execution_posture") or {},
            "object_resolution": doc.get("object_resolution") or {},
            "editor_focus": doc.get("editor_focus") or {},
            "playlist_curation": doc.get("playlist_curation") or {},
            "branch_scope": doc.get("branch_scope") or {},
            "si_goals": doc.get("si_goals") or {},
            "write_quality": doc.get("write_quality") or {},
            "slide_design": doc.get("slide_design") or {},
            "screenshot_parity": doc.get("screenshot_parity") or {},
            "data_discovery": doc.get("data_discovery") or {},
            "data_transform": doc.get("data_transform") or {},
            "compound_slide": doc.get("compound_slide") or {},
            "display_format": doc.get("display_format") or {},
            "presentation_recipes": recipes,
            "media_limits": doc.get("media_limits") or {},
            "mcp_delia": doc.get("mcp_delia") or {},
            "modes": doc.get("modes") or {},
            "write_flow": doc.get("write_flow") or {},
            "anti_patterns": list(doc.get("anti_patterns") or []),
            "auth_errors": doc.get("auth_errors") or {},
        }
