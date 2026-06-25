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



class ChatProductQueryIntentResolutionService:
    @classmethod
    def resolve_product_intent(cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> str:
        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        if ChatProductDescriptionResolutionService.looks_like_description_lookup(message):
            return ChatProductQueryIntent.FULL

        intent = intent_service().detect(message)

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if intent != ChatProductQueryIntent.FULL:
            if (
                intent_service()._looks_like_explicit_playbook_product_scope(normalized)
                or intent_service()._looks_like_price_analysis_question(normalized)
            ):
                return ChatProductQueryIntent.FULL

            return intent

        if intent_service()._looks_like_explicit_playbook_product_scope(normalized):
            return ChatProductQueryIntent.FULL

        if intent_service()._looks_like_price_analysis_question(normalized):
            return ChatProductQueryIntent.FULL

        if intent_service()._looks_like_product_sub_intent(normalized):
            return intent

        inherited = intent_service().infer_intent_from_recent_tool(previous_messages)

        if not inherited:
            return intent

        if intent_service().extract_product_code(message) or intent_service().references_previous_product(message):
            if intent_service()._looks_like_explicit_playbook_product_scope(normalized):
                return ChatProductQueryIntent.FULL

            if intent_service()._looks_like_price_analysis_question(normalized):
                return ChatProductQueryIntent.FULL

            return inherited

        return inherited

    @classmethod
    def resolve_product_code(cls,
        message: str,
        conversation_context: str | None = None,
        *,
        previous_messages: list | None = None,
        user_context_items: list | None = None,
        operational_focus: dict | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        drill_code = ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
            message,
        )

        if drill_code:
            return drill_code

        description_query = ChatProductDescriptionResolutionService.extract_description_query(
            message,
        )

        if description_query:
            resolved = ChatProductDescriptionResolutionService.resolve_code_from_history(
                description_query,
                previous_messages=previous_messages,
            )

            if resolved:
                return resolved

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return intent_service().extract_product_code(message)

        if intent_service().looks_like_scope_reset_operational_query(message):
            return intent_service().extract_product_code(message)

        code = intent_service().extract_product_code(message)

        if code:
            return code

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        if not (
            intent_service().references_previous_product(message)
            or ChatProductQueryIntentContentService._matches_any_predicates(
                ChatProductQueryIntentContentService._code_from_history_predicates(),
                normalized,
            )
            or ChatRouteContextService.segment_from_message(message)
            or ChatRouteContextService.resolve_product_route_segment(
                message,
                previous_messages=previous_messages,
            )
        ):
            from app.domain.services.chat_follow_up_intent_service import (
                ChatFollowUpIntentService,
            )

            if not ChatFollowUpIntentService.is_operational_follow_up(message):
                return None

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        if memory_snapshot and user_context_items is None and operational_focus is None:
            if isinstance(memory_snapshot, dict):
                user_context_items = memory_snapshot.get("userContextItems")
                operational_focus = ChatSnapshotOperationalFocus.get(memory_snapshot)

        if user_context_items is not None:
            code = ChatUserContextItemService.resolve_product_code_from_items(
                user_context_items,
            )

            if code:
                return code

        if isinstance(operational_focus, dict):
            token = str(operational_focus.get("productCode") or "").strip()

            if token and intent_service().is_plausible_product_code(token):
                return token

        if conversation_context:
            code = ChatUserContextItemService.resolve_product_code_from_context_prompt(
                conversation_context,
            )

            if code:
                return code

        if previous_messages:
            code = intent_service().extract_last_product_code_from_messages(previous_messages)

            if code:
                return code

        if conversation_context:
            return intent_service().extract_last_product_code(conversation_context)

        return None

