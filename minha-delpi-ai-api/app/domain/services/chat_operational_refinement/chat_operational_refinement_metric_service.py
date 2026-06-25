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



class ChatOperationalRefinementMetricService:
    @classmethod
    def plan_metric_follow_ups(cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = ChatRouteContextService.collect_recent_metric_route(previous_messages)

        if not recent:
            return []

        branch = refinement_service().extract_branch_code(normalized)

        if ChatRouteContextService.looks_like_metric_scope_reset(normalized):
            return [
                OperationalRefinement(
                    kind="metric_reset",
                    metric_kind=recent.kind,
                    metric_domain_prefix=recent.domain_prefix,
                    metric_path_token=recent.path_token,
                    reason=recent.reason,
                )
            ]

        if not refinement_service().looks_like_operational_refinement(normalized):
            return []

        if not branch and not refinement_service()._requires_stock_refinement(normalized):
            return []

        return [
            OperationalRefinement(
                kind="metric_refinement",
                branch=branch,
                metric_kind=recent.kind,
                metric_domain_prefix=recent.domain_prefix,
                metric_path_token=recent.path_token,
                reason=recent.reason,
            )
        ]

