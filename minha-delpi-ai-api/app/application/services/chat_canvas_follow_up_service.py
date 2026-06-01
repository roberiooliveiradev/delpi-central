"""Chips pós-resposta quando a lousa está ativa — Playbook 05 Fase 4–5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict:
    return ContentService.personality_playbook()


class ChatCanvasFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        workspace_context: dict | None,
        previous_messages: list[Any] | None = None,
        opened_canvas_this_turn: bool = False,
    ) -> None:
        if not cls._canvas_enabled(workspace_context):
            return

        markdown, _, _ = ChatCanvasContentService.find_active_canvas(previous_messages)

        if not markdown and not opened_canvas_this_turn:
            return

        if metadata.get("canvasFollowUpSuggestions"):
            return

        labels = list(_playbook().get("canvasFollowUpChips") or [])
        queries = _playbook().get("canvasFollowUpQueries") or {}

        if not labels:
            return

        suggestions: list[dict[str, str]] = []

        for label in labels[:7]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        if suggestions:
            metadata["canvasFollowUpSuggestions"] = suggestions

    @classmethod
    def _canvas_enabled(cls, workspace_context: dict | None) -> bool:
        capabilities = (workspace_context or {}).get("capabilities") or {}
        canvas = capabilities.get("canvas")

        if isinstance(canvas, bool):
            return canvas

        return True
