"""Chips pós-resposta para tarefas textuais — Playbook 03 §23."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_text_task_service import ChatTextTaskService
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatTextTaskFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        answer: str | None = None,
        workspace_context: dict | None = None,
    ) -> None:
        if not (
            ChatTextTaskService.is_text_task(message)
            or (workspace_context or {}).get("textTaskMode")
        ):
            return

        suggestions = cls.build_suggestions(message)

        if suggestions:
            metadata["textTaskFollowUpSuggestions"] = suggestions

        text_task = ChatTextTaskService.build_text_task_metadata(
            message=message,
            answer=answer,
            workspace_context=workspace_context,
        )

        if text_task and "textTask" not in metadata:
            metadata.update(text_task)

        from app.domain.services.chat_text_quality_validator import ChatTextQualityValidator

        quality = ChatTextQualityValidator.validate(
            answer,
            message=message,
            workspace_context=workspace_context,
        )

        if quality.get("checks"):
            metadata["textTaskQuality"] = quality

        from app.application.services.chat_text_task_metrics_service import (
            ChatTextTaskMetricsService,
        )

        ChatTextTaskMetricsService.attach_to_assistant_metadata(
            metadata,
            message=message,
            workspace_context=workspace_context,
        )

    @classmethod
    def build_suggestions(cls, message: str | None) -> list[dict[str, str]]:
        ctx = ChatTextTaskService.classify(message)
        queries = _playbook().get("textTaskFollowUpQueries") or {}
        labels = list(_playbook().get("textTaskFollowUpChips") or ChatTextTaskService.default_suggestions(
            ctx.get("subtype")
        ))

        suggestions: list[dict[str, str]] = []

        for label in labels[:8]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        return suggestions
