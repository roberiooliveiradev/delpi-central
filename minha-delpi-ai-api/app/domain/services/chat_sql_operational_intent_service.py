"""Perguntas operacionais que exigem SQL analítico (docs do agente), não catálogo REST."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)
from app.domain.services.chat_temporal_intent_service import ChatTemporalIntentService


class ChatSqlOperationalIntentService:
    @classmethod
    def _production_phrases(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "productionPhrases",
        )

    @classmethod
    def _catalog_search_markers(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "catalogSearchMarkers",
        )

    @classmethod
    def _inventory_aggregate_markers(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "inventoryAggregateMarkers",
        )

    @classmethod
    def _sales_aggregate_markers(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "salesAggregateMarkers",
        )

    @classmethod
    def _temporal_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "temporalTerms",
        )

    @classmethod
    def _production_product_scope_phrases(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "operationalIntent",
            "productionProductScopePhrases",
        )

    @classmethod
    def requires_sql_knowledge(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in cls._catalog_search_markers()):
            return False

        if cls._looks_like_aggregate_sql_question(message, normalized):
            return True

        return cls.requires_production_sql_knowledge(message)

    @classmethod
    def requires_production_sql_knowledge(cls, message: str | None) -> bool:
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in cls._catalog_search_markers()):
            return False

        if cls._looks_like_aggregate_sql_question(message, normalized):
            return False

        if any(phrase in normalized for phrase in cls._production_phrases()):
            return True

        if re.search(r"\bproduz\w*\b", normalized) and (
            ChatTemporalIntentService.has_temporal_reference(message)
            or any(term in normalized for term in cls._temporal_terms())
        ):
            if any(
                phrase in normalized
                for phrase in cls._production_product_scope_phrases()
            ):
                return True

        if (
            re.search(r"\bprogramad\w*\b", normalized)
            and re.search(r"\bproduc\w*\b", normalized)
        ):
            return True

        return False

    @classmethod
    def _looks_like_aggregate_sql_question(
        cls,
        message: str | None,
        normalized: str,
    ) -> bool:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if ChatProductQueryIntentService.extract_product_code(message):
            return False

        if ChatProductQueryIntentService.references_previous_product(message):
            return False

        if re.search(r"\bproduto\s+\d", normalized):
            return False

        if any(marker in normalized for marker in cls._inventory_aggregate_markers()):
            return True

        if any(marker in normalized for marker in cls._sales_aggregate_markers()):
            return True

        return False
