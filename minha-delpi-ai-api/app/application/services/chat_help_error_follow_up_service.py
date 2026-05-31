"""Chips de autoajuda após falha operacional — Playbook autoajuda, Fase 5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatHelpErrorFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None = None,
        issues: list[str] | None = None,
        workspace_context: dict | None = None,
    ) -> None:
        suggestions = cls.build(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
            workspace_context=workspace_context,
        )

        if not suggestions:
            return

        metadata["helpErrorFollowUpSuggestions"] = suggestions
        metadata["helpContext"] = "error"

    @classmethod
    def build(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list | None = None,
        issues: list[str] | None = None,
        workspace_context: dict | None = None,
    ) -> list[dict[str, str]]:
        if not cls._should_attach(
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
        ):
            return []

        labels = list(_playbook().get("helpErrorFollowUpChips") or [])
        queries = _playbook().get("helpErrorFollowUpQueries") or {}
        context = workspace_context or {}
        agent = context.get("agent") if isinstance(context.get("agent"), dict) else None
        agent_name = str((agent or {}).get("name") or "").strip()

        if agent_name and "Escolher agente" not in labels:
            labels.append("Escolher agente")

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or "").strip()

            if not template:
                continue

            query = template.replace("{agent_name}", agent_name or "especializado")

            if "{agent_name}" in query and not agent_name:
                query = "como escolho um agente para consultas operacionais?"

            suggestions.append({"label": str(label), "query": query.strip()})

        return suggestions

    @classmethod
    def _should_attach(
        cls,
        *,
        answer: str,
        tool_calls: list | None,
        issues: list[str] | None,
    ) -> bool:
        if issues:
            return True

        outcome = ChatFollowUpSuggestionService.classify_outcome(
            answer=answer,
            tool_calls=tool_calls or [],
            issues=issues,
        )

        return outcome == "error"
