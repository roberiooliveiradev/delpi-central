"""Semântica declarativa de aviso de consolidação multi-filial (listagem vs agregado)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)


class ChatOperationalConsolidationCoverageService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_profiles"

    @classmethod
    def resolve_entity(
        cls,
        *,
        response_meta: dict[str, Any] | None = None,
        path: str | None = None,
    ) -> str | None:
        if isinstance(response_meta, dict):
            entity = str(response_meta.get("entity") or "").strip()

            if entity:
                return entity

        resolved = ChatPresentationProfileService.resolve_entity_from_path(path)

        return str(resolved or "").strip() or None

    @classmethod
    def is_listing_entity(cls, entity: str | None) -> bool:
        token = str(entity or "").strip()

        if not token:
            return False

        listing = cls.node("operationalConsolidationCoverage", "listingEntities")

        if not isinstance(listing, list):
            return False

        return token in {str(item).strip() for item in listing if str(item).strip()}

    @classmethod
    def should_emit_complete_consolidation_notice(cls, entity: str | None) -> bool:
        """Listagens linha a linha não precisam de banner quando completas."""
        return not cls.is_listing_entity(entity)

    @classmethod
    def coverage_message_key(cls, *, entity: str | None, incomplete: bool) -> str:
        keys = cls.node("operationalConsolidationCoverage", "messageKeys")

        if not isinstance(keys, dict):
            keys = {}

        if cls.is_listing_entity(entity):
            fallback = (
                "operationalIncompleteListingAllBranches"
                if incomplete
                else "operationalConsolidatedListingAllBranches"
            )
            slot = "listingIncomplete" if incomplete else "listingComplete"
        else:
            fallback = (
                "operationalIncompleteConsolidated"
                if incomplete
                else "operationalConsolidatedAllBranches"
            )
            slot = "aggregatedIncomplete" if incomplete else "aggregatedComplete"

        return str(keys.get(slot) or fallback).strip() or fallback
