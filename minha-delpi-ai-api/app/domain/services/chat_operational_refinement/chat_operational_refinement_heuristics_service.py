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



class ChatOperationalRefinementHeuristicsService:
    @classmethod
    def looks_like_stock_scope_reset(cls, normalized: str) -> bool:
        return any(term in normalized for term in VOCAB.STOCK_RESET_TERMS)

    @classmethod
    def looks_like_pagination_request(cls, normalized: str) -> bool:
        if refinement_service().extract_requested_page_size(normalized) is not None:
            return True

        if refinement_service().extract_requested_page(normalized) is not None:
            return True

        if refinement_service().looks_like_next_page_request(normalized):
            return True

        if refinement_service().looks_like_prev_page_request(normalized):
            return True

        return refinement_service().looks_like_more_results_request(normalized)

    @classmethod
    def looks_like_next_page_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            VOCAB.NEXT_PAGE_TERMS,
        )

    @classmethod
    def looks_like_prev_page_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            VOCAB.PREV_PAGE_TERMS,
        )

    @classmethod
    def looks_like_more_results_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            VOCAB.MORE_RESULTS_TERMS,
        )

    @classmethod
    def looks_like_depth_increase_request(cls, normalized: str) -> bool:
        if refinement_service().extract_requested_max_depth(normalized) is not None:
            return True

        return ChatMessageNormalizationService.contains_any(
            normalized,
            VOCAB.DEPTH_INCREASE_TERMS,
        )

    @classmethod
    def extract_requested_max_depth(cls, normalized: str) -> int | None:
        match = VOCAB.MAX_DEPTH_RE.search(normalized)

        if not match:
            return None

        value = int(match.group(1))

        if 1 <= value <= 99:
            return value

        return None

    @classmethod
    def _is_operational_navigation_message(cls, normalized: str) -> bool:
        return (
            refinement_service().looks_like_pagination_request(normalized)
            or refinement_service().looks_like_depth_increase_request(normalized)
        )

    @classmethod
    def extract_requested_page_size(cls, normalized: str) -> int | None:
        for pattern in VOCAB.PAGE_SIZE_PATTERNS:
            match = pattern.search(normalized)

            if not match:
                continue

            value = int(match.group(1))

            if 1 <= value <= 500:
                return value

        return None

    @classmethod
    def extract_requested_page(cls, normalized: str) -> int | None:
        match = VOCAB.PAGE_NUMBER_RE.search(normalized)

        if not match:
            return None

        value = int(match.group(1))

        if value >= 1:
            return value

        return None

    @classmethod
    def looks_like_operational_refinement(cls, normalized: str) -> bool:
        if any(term in normalized for term in VOCAB.FILTER_TERMS):
            return True

        if "filial" in normalized and any(
            term in normalized
            for term in ("filtre", "filtro", "filtrar", "só", "so", "apenas", "somente")
        ):
            return True

        if refinement_service().extract_branch_code(normalized):
            return True

        if refinement_service().extract_warehouse_code(normalized):
            return True

        return False

    @classmethod
    def extract_branch_code(cls, normalized: str) -> str | None:
        match = VOCAB.BRANCH_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def extract_warehouse_code(cls, normalized: str) -> str | None:
        match = VOCAB.WAREHOUSE_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def _requires_stock_refinement(cls, normalized: str) -> bool:
        return "filial" in normalized or "armazem" in normalized or "armazém" in normalized

