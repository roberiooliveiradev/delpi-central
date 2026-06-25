"""Delegate — intenção de consulta de produto."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_facade_access import (
    intent_service,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_models import (
    ChatProductQueryIntent,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_vocabulary import (
    ChatProductQueryIntentVocabulary as VOCAB,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"



class ChatProductQueryIntentContextService:
    @classmethod
    def _looks_like_mixed_documental_operational(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )

        return ChatProductQueryIntentDetectionService.looks_like_mixed_documental_operational(
            normalized
        )

    @classmethod
    def references_previous_product(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        terms = [
            *ChatProductQueryIntentContentService._terms("referencesPreviousProduct", "filterTerms"),
            *ChatProductOperationalContentService.list(
                "referencesPreviousProduct",
                "terms",
            ),
        ]

        return any(term in normalized for term in terms) or ChatProductQueryIntentContextService._looks_like_product_followup(
            normalized
        )

    @classmethod
    def _looks_like_product_followup(cls, normalized: str) -> bool:
        has_followup = any(
            term in normalized for term in ChatProductQueryIntentContentService._terms("followUp", "followup")
        )
        has_product_ref = any(
            term in normalized for term in ChatProductQueryIntentContentService._terms("followUp", "productRef")
        )

        return has_followup and has_product_ref

    @classmethod
    def looks_like_scope_reset_operational_query(cls, message: str | None) -> bool:
        """Consulta agregada/temporal — não reaproveitar productCode da sessão."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(
            marker in normalized
            for marker in ChatProductQueryIntentContentService._terms("scopeReset", "markers")
        ):
            return True

        if intent_service().references_previous_product(message):
            return False

        if re.search(r"\b20\d{2}\b", normalized) and any(
            term in normalized for term in ChatProductQueryIntentContentService._terms("scopeReset", "temporal")
        ):
            return True

        return False

    @classmethod
    def should_inherit_product_code(cls, message: str | None) -> bool:
        from app.domain.services.chat_project_sources_intent_service import (
            ChatProjectSourcesIntentService,
        )

        if ChatProjectSourcesIntentService.is_content_question(message):
            return False

        if intent_service().looks_like_scope_reset_operational_query(message):
            return False

        if intent_service().extract_product_code(message):
            return True

        if intent_service().references_previous_product(message):
            return True

        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )

        return ChatFollowUpIntentService.is_operational_follow_up(message)

    @classmethod
    def infer_intent_from_recent_tool(cls, previous_messages: list | None) -> str | None:
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        segment = ChatRouteContextService.infer_product_route_segment_from_recent_tool(
            previous_messages
        )

        if not segment:
            return None

        intent = ChatRouteContextService.intent_for_product_segment(segment)

        if intent:
            return intent

        if ChatRouteContextService.is_product_route_segment(segment):
            return ChatProductQueryIntent.FULL

        return None

