"""Fachada pública — refinamentos operacionais em cima do turno anterior."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_refinement.chat_operational_refinement_group_by_service import (
    ChatOperationalRefinementGroupByService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_heuristics_service import (
    ChatOperationalRefinementHeuristicsService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_metric_service import (
    ChatOperationalRefinementMetricService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_models import (
    OperationalRefinement,
    RecentPaginatedAction,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_orchestration_service import (
    ChatOperationalRefinementOrchestrationService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_pagination_service import (
    ChatOperationalRefinementPaginationService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_stock_service import (
    ChatOperationalRefinementStockService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_support_service import (
    ChatOperationalRefinementSupportService,
)

__all__ = [
    "ChatOperationalRefinementService",
    "OperationalRefinement",
    "RecentPaginatedAction",
]


class ChatOperationalRefinementService:
    """API estável — detect, plan_* e heurísticas de refinamento operacional."""

    @classmethod
    def plan_operational_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementOrchestrationService.plan_operational_follow_ups(
            *args, **kwargs
        )

    @classmethod
    def detect(cls, *args, **kwargs) -> OperationalRefinement | None:
        return ChatOperationalRefinementOrchestrationService.detect(*args, **kwargs)

    @classmethod
    def is_operational_follow_up(cls, *args, **kwargs) -> bool:
        return ChatOperationalRefinementOrchestrationService.is_operational_follow_up(
            *args, **kwargs
        )

    @classmethod
    def plan_pagination_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementPaginationService.plan_pagination_follow_ups(
            *args, **kwargs
        )

    @classmethod
    def plan_depth_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementPaginationService.plan_depth_follow_ups(*args, **kwargs)

    @classmethod
    def plan_operational_group_by_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementGroupByService.plan_operational_group_by_follow_ups(
            *args, **kwargs
        )

    @classmethod
    def plan_metric_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementMetricService.plan_metric_follow_ups(*args, **kwargs)

    @classmethod
    def plan_stock_follow_ups(cls, *args, **kwargs) -> list[OperationalRefinement]:
        return ChatOperationalRefinementStockService.plan_stock_follow_ups(*args, **kwargs)

    @classmethod
    def collect_recent_paginated_action(cls, *args, **kwargs) -> RecentPaginatedAction | None:
        return ChatOperationalRefinementPaginationService.collect_recent_paginated_action(
            *args, **kwargs
        )

    @classmethod
    def looks_like_stock_scope_reset(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_stock_scope_reset(normalized)

    @classmethod
    def looks_like_pagination_request(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_pagination_request(normalized)

    @classmethod
    def looks_like_next_page_request(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_next_page_request(normalized)

    @classmethod
    def looks_like_prev_page_request(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_prev_page_request(normalized)

    @classmethod
    def looks_like_more_results_request(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_more_results_request(normalized)

    @classmethod
    def looks_like_depth_increase_request(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_depth_increase_request(
            normalized
        )

    @classmethod
    def looks_like_operational_refinement(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService.looks_like_operational_refinement(
            normalized
        )

    @classmethod
    def extract_requested_max_depth(cls, normalized: str) -> int | None:
        return ChatOperationalRefinementHeuristicsService.extract_requested_max_depth(normalized)

    @classmethod
    def extract_requested_page_size(cls, normalized: str) -> int | None:
        return ChatOperationalRefinementHeuristicsService.extract_requested_page_size(normalized)

    @classmethod
    def extract_requested_page(cls, normalized: str) -> int | None:
        return ChatOperationalRefinementHeuristicsService.extract_requested_page(normalized)

    @classmethod
    def extract_branch_code(cls, normalized: str) -> str | None:
        return ChatOperationalRefinementHeuristicsService.extract_branch_code(normalized)

    @classmethod
    def extract_warehouse_code(cls, normalized: str) -> str | None:
        return ChatOperationalRefinementHeuristicsService.extract_warehouse_code(normalized)

    # --- Delegates privados (cross-module via fachada) ---

    @classmethod
    def _requires_stock_refinement(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService._requires_stock_refinement(normalized)

    @classmethod
    def _is_operational_navigation_message(cls, normalized: str) -> bool:
        return ChatOperationalRefinementHeuristicsService._is_operational_navigation_message(
            normalized
        )

    @classmethod
    def _has_recent_stock_context(cls, *args, **kwargs) -> bool:
        return ChatOperationalRefinementStockService._has_recent_stock_context(*args, **kwargs)

    @classmethod
    def _collect_recent_stock_product_codes(cls, *args, **kwargs) -> list[str]:
        return ChatOperationalRefinementStockService._collect_recent_stock_product_codes(
            *args, **kwargs
        )

    @classmethod
    def _product_code_from_messages(cls, *args, **kwargs) -> str | None:
        return ChatOperationalRefinementStockService._product_code_from_messages(*args, **kwargs)

    @classmethod
    def _parameter_int(cls, *args, **kwargs) -> int | None:
        return ChatOperationalRefinementSupportService._parameter_int(*args, **kwargs)

    @classmethod
    def _parameter_str(cls, *args, **kwargs) -> str | None:
        return ChatOperationalRefinementSupportService._parameter_str(*args, **kwargs)

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        return ChatOperationalRefinementSupportService._message_metadata(message)

    @classmethod
    def _message_content(cls, message: Any) -> str:
        return ChatOperationalRefinementSupportService._message_content(message)

    @classmethod
    def _message_field_role(cls, message: Any) -> str:
        return ChatOperationalRefinementSupportService._message_field_role(message)

    @classmethod
    def _route_segment_from_path(cls, path: str) -> str | None:
        return ChatOperationalRefinementPaginationService._route_segment_from_path(path)

    @classmethod
    def _has_paginated_coverage(cls, coverage: dict | None) -> bool:
        return ChatOperationalRefinementPaginationService._has_paginated_coverage(coverage)

    @classmethod
    def _is_paginated_path(cls, path: str) -> bool:
        return ChatOperationalRefinementPaginationService._is_paginated_path(path)

    @classmethod
    def _resolve_pagination_state(cls, *args, **kwargs):
        return ChatOperationalRefinementPaginationService._resolve_pagination_state(*args, **kwargs)

    @classmethod
    def _infer_paginated_route_segment(cls, *args, **kwargs) -> str | None:
        return ChatOperationalRefinementPaginationService._infer_paginated_route_segment(
            *args, **kwargs
        )

    @classmethod
    def _coerce_int(cls, value: Any) -> int | None:
        return ChatOperationalRefinementPaginationService._coerce_int(value)

    @classmethod
    def _resolve_page_size_from_parameters(cls, parameters: dict) -> int | None:
        return ChatOperationalRefinementPaginationService._resolve_page_size_from_parameters(
            parameters
        )

    @classmethod
    def _collect_recent_paginated_action_from_tool_calls(cls, *args, **kwargs):
        return ChatOperationalRefinementPaginationService._collect_recent_paginated_action_from_tool_calls(
            *args, **kwargs
        )

    @classmethod
    def _collect_recent_paginated_action_from_context(cls, *args, **kwargs):
        return ChatOperationalRefinementPaginationService._collect_recent_paginated_action_from_context(
            *args, **kwargs
        )

    @classmethod
    def _extract_latest_operational_snapshot(cls, *args, **kwargs) -> dict | None:
        return ChatOperationalRefinementPaginationService._extract_latest_operational_snapshot(
            *args, **kwargs
        )
