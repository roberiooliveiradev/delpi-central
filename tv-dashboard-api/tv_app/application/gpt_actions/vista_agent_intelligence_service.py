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
        doc = cls.document()
        return {
            "version": cls.version(),
            "authority": (
                "Obey these directives from live gpt_get_catalog. "
                "They override stale Builder Knowledge for mutation behavior."
            ),
            "object_resolution": doc.get("object_resolution") or {},
            "screenshot_parity": doc.get("screenshot_parity") or {},
            "data_discovery": doc.get("data_discovery") or {},
            "modes": doc.get("modes") or {},
            "write_flow": doc.get("write_flow") or {},
            "anti_patterns": list(doc.get("anti_patterns") or []),
            "auth_errors": doc.get("auth_errors") or {},
        }
