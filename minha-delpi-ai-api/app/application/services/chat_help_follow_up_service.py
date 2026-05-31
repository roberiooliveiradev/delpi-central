"""Chips de exploração após respostas de autoajuda — Playbook autoajuda, Fase 1."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatHelpFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(cls, metadata: dict, *, message: str) -> None:
        suggestions = cls.build(message=message)

        if suggestions:
            metadata["helpFollowUpSuggestions"] = suggestions

    @classmethod
    def build(cls, *, message: str) -> list[dict[str, str]]:
        if not ChatCapabilitiesService.is_capability_inquiry(message):
            return []

        topic = ChatCapabilitiesService.classify_help_topic(message)
        queries = _playbook().get("helpFollowUpQueries") or {}

        if ChatCapabilitiesService.is_capabilities_question(message):
            labels = list(_playbook().get("helpFollowUpChipsGeneral") or [])
        elif topic:
            by_topic = _playbook().get("helpFollowUpChipsByTopic") or {}
            labels = list(by_topic.get(topic) or [])
        else:
            labels = list(_playbook().get("helpFollowUpChipsGeneral") or [])

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()

            if not template:
                continue

            suggestions.append({"label": str(label), "query": template})

        return suggestions
