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
            labels = cls._labels_from_registry(topic)
            by_topic = _playbook().get("helpFollowUpChipsByTopic") or {}
            labels.extend(list(by_topic.get(topic) or []))
            labels = cls._dedupe_labels(labels)
        else:
            labels = list(_playbook().get("helpFollowUpChipsGeneral") or [])

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or "").strip()

            if not template:
                template = cls._query_from_registry_title(label)

            if not template:
                template = str(label).strip()

            if not template:
                continue

            suggestions.append({"label": str(label), "query": template})

        return suggestions

    @classmethod
    def _labels_from_registry(cls, topic: str) -> list[str]:
        from app.application.services.assistant_capabilities_registry import (
            AssistantCapabilitiesRegistry,
        )

        feature = AssistantCapabilitiesRegistry.find_by_help_topic(topic)

        if not feature:
            return []

        labels: list[str] = []
        related = feature.get("relatedFeatures") or []

        for feature_id in related:
            related_feature = AssistantCapabilitiesRegistry.get_feature(str(feature_id))

            if not related_feature:
                continue

            title = str(related_feature.get("title") or "").strip()

            if title:
                labels.append(title)

        return labels[:4]

    @classmethod
    def _query_from_registry_title(cls, title: str) -> str:
        from app.application.services.assistant_capabilities_registry import (
            AssistantCapabilitiesRegistry,
        )

        cleaned = str(title or "").strip()

        for feature in AssistantCapabilitiesRegistry.list_features():
            if str(feature.get("title") or "").strip() != cleaned:
                continue

            examples = feature.get("examples") or []

            if isinstance(examples, list) and examples:
                return str(examples[0]).strip()

        return ""

    @staticmethod
    def _dedupe_labels(labels: list) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for label in labels:
            cleaned = str(label or "").strip()

            if not cleaned or cleaned in seen:
                continue

            seen.add(cleaned)
            ordered.append(cleaned)

        return ordered
