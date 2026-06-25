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



class ChatOperationalRefinementGroupByService:
    @classmethod
    def plan_operational_group_by_follow_ups(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        from app.domain.services.chat_operational_group_by_refinement_service import (
            ChatOperationalGroupByRefinementService,
        )

        plan = ChatOperationalGroupByRefinementService.plan_refetch_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not plan:
            return []

        return [
            OperationalRefinement(
                kind="operational_group_by_refinement",
                action_id=plan.action_id or None,
                previous_parameters=dict(plan.parameters),
                previous_path=plan.path,
                group_by=plan.refetch_group_by or plan.dimension,
                operational_route_id=plan.route_id or None,
                group_by_label=plan.dimension_label or None,
                reason="",
            )
        ]

