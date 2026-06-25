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



class ChatOperationalRefinementPaginationService:
    @classmethod
    def plan_pagination_follow_ups(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = refinement_service().collect_recent_paginated_action(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not recent or not refinement_service().looks_like_pagination_request(normalized):
            return []

        page_size = refinement_service().extract_requested_page_size(normalized)
        page = refinement_service().extract_requested_page(normalized)

        if page is None and refinement_service().looks_like_next_page_request(normalized):
            current_page = recent.page or refinement_service()._parameter_int(recent.parameters, "page") or 1
            page = current_page + 1

        if page is None and refinement_service().looks_like_prev_page_request(normalized):
            current_page = recent.page or refinement_service()._parameter_int(recent.parameters, "page") or 1
            page = max(1, current_page - 1)

        if page is None and page_size is None and refinement_service().looks_like_more_results_request(normalized):
            current_page = recent.page or refinement_service()._parameter_int(recent.parameters, "page") or 1
            page = current_page + 1

        if page is None and page_size is None:
            return []

        return [
            OperationalRefinement(
                kind="pagination_refinement",
                action_id=recent.action_id or None,
                product_code=recent.product_code,
                route_segment=recent.route_segment,
                previous_parameters=dict(recent.parameters),
                previous_path=recent.path,
                page=page,
                page_size=page_size,
                reason=(
                    "A mensagem ajusta paginação da consulta operacional já feita nesta conversa."
                ),
            )
        ]

    @classmethod
    def plan_depth_follow_ups(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not refinement_service().looks_like_depth_increase_request(normalized):
            return []

        recent = refinement_service().collect_recent_paginated_action(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not recent or recent.route_segment not in {"parents", "structure"}:
            return []

        requested_depth = refinement_service().extract_requested_max_depth(normalized)
        current_depth = refinement_service()._parameter_int(recent.parameters, "max_depth")
        depth_cap = (
            15
            if recent.route_segment in {"parents", "structure"}
            else 99
        )
        max_depth = requested_depth or (current_depth + 5 if current_depth else depth_cap)
        max_depth = min(max(max_depth, 1), depth_cap)

        return [
            OperationalRefinement(
                kind="depth_refinement",
                action_id=recent.action_id or None,
                product_code=recent.product_code,
                route_segment=recent.route_segment,
                previous_parameters=dict(recent.parameters),
                previous_path=recent.path,
                page=recent.page or refinement_service()._parameter_int(recent.parameters, "page"),
                page_size=recent.page_size or refinement_service()._parameter_int(recent.parameters, "page_size"),
                max_depth=max_depth,
                reason=(
                    "A mensagem amplia a profundidade da consulta hierárquica já feita nesta conversa."
                ),
            )
        ]

    @classmethod
    def collect_recent_paginated_action(cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> RecentPaginatedAction | None:
        from_tool_calls = cls._collect_recent_paginated_action_from_tool_calls(previous_messages)

        if from_tool_calls:
            return from_tool_calls

        return cls._collect_recent_paginated_action_from_context(
            previous_messages,
            conversation_context=conversation_context,
        )

    @classmethod
    def _collect_recent_paginated_action_from_tool_calls(cls,
        previous_messages: list[Any] | None,
    ) -> RecentPaginatedAction | None:
        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(refinement_service()._message_metadata(item).get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")
                lowered_path = path.lower()
                coverage = tool_meta.get("dataCoverageNotice")

                if not refinement_service()._has_paginated_coverage(coverage) and not refinement_service()._is_paginated_path(
                    lowered_path
                ):
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                action_id = str(
                    tool_meta.get("actionId")
                    or arguments.get("actionId")
                    or ""
                ).strip()

                product_code = refinement_service()._parameter_str(parameters, "code")
                route_segment = refinement_service()._route_segment_from_path(path)
                page, page_size = refinement_service()._resolve_pagination_state(
                    parameters,
                    coverage if isinstance(coverage, dict) else None,
                )

                if not action_id:
                    if not product_code:
                        from app.domain.services.chat_analysis_intent_service import (
                            ChatAnalysisIntentService,
                        )

                        product_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                            path,
                        )

                    if product_code and route_segment:
                        return RecentPaginatedAction(
                            action_id="",
                            path=path,
                            parameters=dict(parameters),
                            page=page,
                            page_size=page_size,
                            product_code=product_code,
                            route_segment=route_segment,
                        )

                    continue

                return RecentPaginatedAction(
                    action_id=action_id,
                    path=path,
                    parameters=dict(parameters),
                    page=page,
                    page_size=page_size,
                    product_code=product_code,
                    route_segment=route_segment,
                )

        return None

    @classmethod
    def _collect_recent_paginated_action_from_context(cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> RecentPaginatedAction | None:
        product_code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
            previous_messages or [],
        )

        if not product_code:
            return None

        route_segment = refinement_service()._infer_paginated_route_segment(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not route_segment:
            return None

        snapshot = refinement_service()._extract_latest_operational_snapshot(
            previous_messages,
            conversation_context=conversation_context,
        )
        page = snapshot.get("page") if snapshot else None
        page_size = snapshot.get("page_size") if snapshot else None
        parameters = dict(snapshot.get("parameters") or {}) if snapshot else {}

        path = f"/products/{product_code}/{route_segment}"
        parameters.setdefault("code", product_code)
        parameters.setdefault("page", page or 1)
        parameters.setdefault("page_size", page_size or 25)

        return RecentPaginatedAction(
            action_id=str(snapshot.get("action_id") or "") if snapshot else "",
            path=str(snapshot.get("path") or path) if snapshot else path,
            parameters=parameters,
            page=page or refinement_service()._parameter_int(parameters, "page") or 1,
            page_size=page_size or refinement_service()._parameter_int(parameters, "page_size") or 25,
            product_code=product_code,
            route_segment=route_segment,
        )

    @classmethod
    def _extract_latest_operational_snapshot(cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> dict[str, Any] | None:
        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(refinement_service()._message_metadata(item).get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")

                if not any(
                    fragment in path.lower()
                    for fragment in VOCAB.PAGINATED_PATH_FRAGMENTS
                ):
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                coverage = tool_meta.get("dataCoverageNotice")
                page, page_size = refinement_service()._resolve_pagination_state(
                    parameters,
                    coverage if isinstance(coverage, dict) else None,
                )

                return {
                    "action_id": str(
                        tool_meta.get("actionId")
                        or arguments.get("actionId")
                        or ""
                    ).strip(),
                    "path": path,
                    "parameters": dict(parameters),
                    "page": page,
                    "page_size": page_size,
                }

        context = str(conversation_context or "").lower()

        for fragment in VOCAB.PAGINATED_PATH_FRAGMENTS:
            if fragment in context:
                return {"path": fragment}

        return None

    @classmethod
    def _has_paginated_coverage(cls, coverage: dict | None) -> bool:
        if not isinstance(coverage, dict):
            return False

        kind = str(coverage.get("kind") or "").lower()

        if kind == "pagination":
            return True

        details = coverage.get("details")

        if not isinstance(details, dict):
            return False

        for key in ("pagination", "structurePagination", "stockPagination"):
            if isinstance(details.get(key), dict):
                return True

        preview = details.get("tablePreview")

        if isinstance(preview, dict):
            total = cls._coerce_int(preview.get("total"))
            shown = cls._coerce_int(preview.get("shown"))

            if total is not None and shown is not None and total > shown:
                return True

        return False

    @classmethod
    def _is_paginated_path(cls, path: str) -> bool:
        lowered = str(path or "").lower()

        return any(fragment in lowered for fragment in VOCAB.PAGINATED_PATH_FRAGMENTS)

    @classmethod
    def _resolve_page_size_from_parameters(cls, parameters: dict) -> int | None:
        for key in ("page_size", "pagesize", "limit"):
            value = refinement_service()._parameter_int(parameters, key)

            if value is not None:
                return value

        return None

    @classmethod
    def _resolve_pagination_state(cls,
        parameters: dict,
        coverage: dict | None,
    ) -> tuple[int | None, int | None]:
        page = refinement_service()._parameter_int(parameters, "page")
        page_size = cls._resolve_page_size_from_parameters(parameters)

        if not isinstance(coverage, dict):
            return page, page_size

        details = coverage.get("details")

        if not isinstance(details, dict):
            return page, page_size

        for key in ("pagination", "structurePagination", "stockPagination"):
            pagination = details.get(key)

            if not isinstance(pagination, dict):
                continue

            page = cls._coerce_int(pagination.get("page")) or page
            page_size = cls._coerce_int(pagination.get("pageSize")) or page_size
            break

        if page_size is None:
            preview = details.get("tablePreview")

            if isinstance(preview, dict):
                page_size = cls._coerce_int(preview.get("shown")) or page_size

        return page, page_size

    @classmethod
    def _coerce_int(cls, value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None

        if parsed >= 1:
            return parsed

        return None

    @classmethod
    def _infer_paginated_route_segment(cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> str | None:
        context = str(conversation_context or "").lower()

        for fragment, segment in (
            ("/parents", "parents"),
            ("/structure", "structure"),
            ("/stock", "stock"),
            ("/search", "search"),
        ):
            if fragment in context:
                return segment

        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(refinement_service()._message_metadata(item).get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                route_segment = refinement_service()._route_segment_from_path(str(tool_meta.get("path") or ""))

                if route_segment:
                    return route_segment

        for item in reversed((previous_messages or [])[-14:]):
            if refinement_service()._message_field_role(item) != "user":
                continue

            normalized = ChatMessageNormalizationService.normalize_for_matching(
                refinement_service()._message_content(item),
            )

            if refinement_service()._is_operational_navigation_message(normalized):
                continue

            intent = ChatProductQueryIntentService.detect(normalized)

            if intent == ChatProductQueryIntent.PARENTS:
                return "parents"

            if intent == ChatProductQueryIntent.STRUCTURE:
                return "structure"

            if intent == ChatProductQueryIntent.STOCK:
                return "stock"

            if "onde e usado" in normalized or "produtos pai" in normalized:
                return "parents"

        return None

    @classmethod
    def _route_segment_from_path(cls, path: str) -> str | None:
        lowered = str(path or "").lower()

        for segment in ("parents", "structure", "stock", "search"):
            if f"/{segment}" in lowered:
                return segment

        return None

