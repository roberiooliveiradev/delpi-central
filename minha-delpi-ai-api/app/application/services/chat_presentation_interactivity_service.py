"""Chips pós-resposta para tabelas, gráficos e árvores — Playbook 07."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatPresentationInteractivityService:
    @classmethod
    def build_from_tool_calls(cls, tool_calls: list | None) -> list[dict[str, str]]:
        presentation_type = cls._detect_presentation_type(tool_calls)

        if not presentation_type:
            return []

        chip_labels = list(
            (_content().get("presentationChips") or {}).get(presentation_type) or []
        )
        queries = _content().get("presentationQueries") or {}
        suggestions: list[dict[str, str]] = []

        for label in chip_labels[:6]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        return suggestions

    @classmethod
    def _detect_presentation_type(cls, tool_calls: list | None) -> str | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            presentation = metadata.get("presentation")

            if not isinstance(presentation, dict):
                continue

            token = str(presentation.get("type") or "").strip().lower()

            if token in {"table", "chart", "tree", "kpi", "dashboard"}:
                return "kpi" if token == "dashboard" else token

        return None
