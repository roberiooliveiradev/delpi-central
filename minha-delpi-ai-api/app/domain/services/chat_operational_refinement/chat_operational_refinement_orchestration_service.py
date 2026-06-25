"""Delegate — refinamento operacional."""

from __future__ import annotations

import json
import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_route_context_service import (
    ChatRouteContextService,
)

from app.domain.services.chat_operational_refinement.chat_operational_refinement_facade_access import (
    refinement_service,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_models import (
    OperationalRefinement,
    RecentPaginatedAction,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_vocabulary import (
    ChatOperationalRefinementVocabulary as VOCAB,
)



class ChatOperationalRefinementOrchestrationService:
    @classmethod
    def plan_operational_follow_ups(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        planned = refinement_service().plan_stock_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = refinement_service().plan_pagination_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = refinement_service().plan_operational_group_by_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = refinement_service().plan_depth_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        return refinement_service().plan_metric_follow_ups(
            message,
            previous_messages=previous_messages,
        )

    @classmethod
    def detect(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalRefinement | None:
        planned = refinement_service().plan_operational_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not planned:
            return None

        return planned[0]

    @classmethod
    def is_operational_follow_up(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if refinement_service().plan_operational_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        branch = refinement_service().extract_branch_code(normalized)
        warehouse = refinement_service().extract_warehouse_code(normalized)

        if branch or warehouse:
            if ChatRouteContextService.collect_recent_metric_route(previous_messages):
                return True

            if refinement_service()._has_recent_stock_context(
                conversation_context=conversation_context,
                previous_messages=previous_messages,
            ):
                return True

        if not ChatProductQueryIntentService.references_previous_product(message):
            return False

        if refinement_service()._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        if ChatRouteContextService.collect_recent_metric_route(previous_messages):
            return True

        return bool(
            ChatRouteContextService.collect_recent_product_route_batch(previous_messages)
        )

