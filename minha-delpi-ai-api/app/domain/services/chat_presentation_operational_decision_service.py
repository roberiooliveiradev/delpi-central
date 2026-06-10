"""Decisão operacional por perfil + vocabulário — Playbook 12 R5."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationOperationalDecisionService:
    @classmethod
    def should_prefer_tree_primary(
        cls,
        *,
        path: str | None,
        entity: str | None,
        intent_token: str,
        message: str,
        has_tree: bool,
    ) -> bool:
        if not has_tree:
            return False

        if ChatPresentationProfileService.has_flag(path, "tree", entity=entity):
            return True

        if ChatPresentationProfileService.has_flag(path, "analyser", entity=entity):
            return True

        config = ChatPresentationProfileService.presentation_decision_config(path, entity)

        if config.get("preferTreeOnStructureIntent") is True:
            return True

        if cls._matches_intent_markers(intent_token, "structureIntent"):
            return True

        return cls._matches_message_markers(message, "structureMessage")

    @classmethod
    def should_prefer_pricing_narrative(
        cls,
        *,
        path: str | None,
        entity: str | None,
        intent_token: str,
        message: str,
        row_count: int,
        has_text: bool,
    ) -> bool:
        if not has_text:
            return False

        config = ChatPresentationProfileService.presentation_decision_config(path, entity)
        max_rows = int(config.get("narrativeFirstMaxRows") or 12)

        if row_count > max_rows:
            return False

        if ChatPresentationProfileService.has_flag(path, "sale_pricing", entity=entity):
            return True

        if cls._matches_intent_markers(intent_token, "pricingIntent"):
            return True

        return cls._matches_message_markers(message, "pricingMessage")

    @classmethod
    def should_prefer_stock_narrative(
        cls,
        *,
        path: str | None,
        entity: str | None,
        intent_token: str,
        message: str,
        row_count: int,
        has_text: bool,
        has_chart: bool,
    ) -> bool:
        if not has_text or has_chart:
            return False

        if not ChatPresentationProfileService.has_flag(path, "stock", entity=entity):
            if not cls._matches_intent_markers(intent_token, "stockIntent"):
                return False

        config = ChatPresentationProfileService.presentation_decision_config(path, entity)
        max_rows = int(config.get("narrativeFirstMaxRows") or 6)

        if row_count > max_rows:
            return False

        if cls._matches_message_markers(message, "stockMessage"):
            return True

        return ChatPresentationProfileService.has_flag(path, "stock", entity=entity) or cls._matches_intent_markers(
            intent_token,
            "stockIntent",
        )

    @classmethod
    def should_prefer_stock_table_over_chart(
        cls,
        *,
        path: str | None,
        entity: str | None,
        intent_token: str,
        row_count: int,
        has_chart: bool,
    ) -> bool:
        if not has_chart:
            return False

        config = ChatPresentationProfileService.presentation_decision_config(path, entity)
        max_rows = int(config.get("tablePreferredMaxRows") or 3)

        if row_count > max_rows:
            return False

        return ChatPresentationProfileService.has_flag(path, "stock", entity=entity) or cls._matches_intent_markers(
            intent_token,
            "stockIntent",
        )

    @classmethod
    def should_prefer_analyser_text_stack(
        cls,
        *,
        path: str | None,
        entity: str | None,
        has_text: bool,
    ) -> bool:
        if not has_text:
            return False

        return ChatPresentationProfileService.has_flag(path, "analyser", entity=entity)

    @classmethod
    def _matches_intent_markers(cls, intent_token: str, group_key: str) -> bool:
        token = str(intent_token or "").strip().lower()

        if not token:
            return False

        return any(marker in token for marker in ChatPresentationVocabularyService.operational_decision_markers(group_key))

    @classmethod
    def _matches_message_markers(cls, message: str, group_key: str) -> bool:
        token = str(message or "").strip().lower()

        if not token:
            return False

        return any(marker in token for marker in ChatPresentationVocabularyService.operational_decision_markers(group_key))
