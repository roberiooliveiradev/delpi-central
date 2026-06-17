"""Refinamentos operacionais em cima do turno anterior (filtro de filial, etc.)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
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


@dataclass(frozen=True)
class RecentPaginatedAction:
    action_id: str
    path: str
    parameters: dict[str, Any]
    page: int | None = None
    page_size: int | None = None
    product_code: str | None = None
    route_segment: str | None = None


@dataclass(frozen=True)
class OperationalRefinement:
    kind: str
    product_code: str | None = None
    branch: str | None = None
    warehouse: str | None = None
    reason: str = ""
    route_segment: str | None = None
    metric_domain_prefix: str | None = None
    metric_path_token: str | None = None
    metric_kind: str | None = None
    action_id: str | None = None
    previous_parameters: dict[str, Any] | None = None
    previous_path: str | None = None
    page: int | None = None
    page_size: int | None = None
    max_depth: int | None = None
    group_by: str | None = None
    operational_route_id: str | None = None
    group_by_label: str | None = None

    @property
    def clears_branch_filter(self) -> bool:
        return self.kind in {"stock_reset", "metric_reset"}


class ChatOperationalRefinementService:
    _FILTER_TERMS = (
        "filtre",
        "filtro",
        "filtrar",
        "filtra ",
        "mostre só",
        "mostre so",
        "só a filial",
        "so a filial",
        "apenas filial",
        "somente filial",
        "somente a filial",
        "restrinja",
        "restringe",
        "limitar a filial",
        "limita a filial",
    )
    _BRANCH_RE = re.compile(
        r"\b(?:filial|fil\.?)\s*[_-]?\s*(\d{1,2})\b",
        re.IGNORECASE,
    )
    _WAREHOUSE_RE = re.compile(
        r"\b(?:armaz[eé]m|arm\.?|deposito|depósito)\s*[_-]?\s*(\d{1,3})\b",
        re.IGNORECASE,
    )
    _PAGINATED_PATH_FRAGMENTS = (
        "/parents",
        "/structure",
        "/search",
        "/stock",
        "/purchases",
        "/inspection",
        "/guide",
        "/dashboard",
        "/items",
        "/columns",
        "/system/tables",
    )
    _NEXT_PAGE_TERMS = (
        "proxima pagina",
        "proxima pag",
        "seguinte pagina",
        "pagina seguinte",
        "next page",
    )
    _PREV_PAGE_TERMS = (
        "pagina anterior",
        "pagina previa",
        "pagina prev",
        "previous page",
        "voltar pagina",
        "pagina de tras",
    )
    _DEPTH_INCREASE_TERMS = (
        "mais niveis",
        "aprofundar",
        "ampliar niveis",
        "aumentar profundidade",
        "aumente a profundidade",
        "todos os niveis",
        "ver mais niveis",
        "expandir niveis",
        "max depth",
        "max_depth",
    )
    _MAX_DEPTH_RE = re.compile(
        r"\b(?:max[_-]?depth|profundidade|niveis)\s*(?:para\s+)?(\d{1,3})\b",
        re.IGNORECASE,
    )
    _MORE_RESULTS_TERMS = (
        "mais registros",
        "mais linhas",
        "mais resultados",
        "mais itens",
        "ver mais",
        "mostrar mais",
        "traga mais",
        "exiba mais",
    )
    _PAGE_SIZE_PATTERNS = (
        re.compile(
            r"\b(?:aumente|aumenta|mostre|traga|exiba|liste|coloque|mude|altere|"
            r"passar?|colocar?)\s+(?:para\s+)?(\d{1,4})\s*"
            r"(?:linhas?|registros?|itens?|resultados?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:aumente|aumenta)\s+(?:o\s+)?(?:page[_-]?size|tamanho\s+da\s+pagina|"
            r"tamanho\s+da\s+página)\s+(?:para\s+)?(\d{1,4})\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bpage[_-]?size\s*[=:]?\s*(\d{1,4})\b", re.IGNORECASE),
        re.compile(
            r"\b(\d{1,4})\s*(?:linhas?|registros?|itens?|resultados?)\b",
            re.IGNORECASE,
        ),
    )
    _PAGE_NUMBER_RE = re.compile(r"\bp[aá]gina\s*(\d+)\b", re.IGNORECASE)
    _STOCK_RESET_TERMS = (
        "completo de novo",
        "estoque completo",
        "completo novamente",
        "tudo de novo",
        "todas as filiais",
        "todas filiais",
        "todas as filial",
        "sem filtro",
        "sem filial",
        "remova o filtro",
        "remover filtro",
        "tire o filtro",
        "mostre completo",
        "mostra completo",
        "visao completa",
        "visão completa",
    )

    @classmethod
    def looks_like_stock_scope_reset(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._STOCK_RESET_TERMS)

    @classmethod
    def plan_operational_follow_ups(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        planned = cls.plan_stock_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = cls.plan_pagination_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = cls.plan_operational_group_by_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        planned = cls.plan_depth_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if planned:
            return planned

        return cls.plan_metric_follow_ups(
            message,
            previous_messages=previous_messages,
        )

    @classmethod
    def plan_pagination_follow_ups(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = cls.collect_recent_paginated_action(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not recent or not cls.looks_like_pagination_request(normalized):
            return []

        page_size = cls.extract_requested_page_size(normalized)
        page = cls.extract_requested_page(normalized)

        if page is None and cls.looks_like_next_page_request(normalized):
            current_page = recent.page or cls._parameter_int(recent.parameters, "page") or 1
            page = current_page + 1

        if page is None and cls.looks_like_prev_page_request(normalized):
            current_page = recent.page or cls._parameter_int(recent.parameters, "page") or 1
            page = max(1, current_page - 1)

        if page is None and page_size is None and cls.looks_like_more_results_request(normalized):
            current_page = recent.page or cls._parameter_int(recent.parameters, "page") or 1
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
    def plan_operational_group_by_follow_ups(
        cls,
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

    @classmethod
    def plan_depth_follow_ups(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not cls.looks_like_depth_increase_request(normalized):
            return []

        recent = cls.collect_recent_paginated_action(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not recent or recent.route_segment not in {"parents", "structure"}:
            return []

        requested_depth = cls.extract_requested_max_depth(normalized)
        current_depth = cls._parameter_int(recent.parameters, "max_depth")
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
                page=recent.page or cls._parameter_int(recent.parameters, "page"),
                page_size=recent.page_size or cls._parameter_int(recent.parameters, "page_size"),
                max_depth=max_depth,
                reason=(
                    "A mensagem amplia a profundidade da consulta hierárquica já feita nesta conversa."
                ),
            )
        ]

    @classmethod
    def looks_like_pagination_request(cls, normalized: str) -> bool:
        if cls.extract_requested_page_size(normalized) is not None:
            return True

        if cls.extract_requested_page(normalized) is not None:
            return True

        if cls.looks_like_next_page_request(normalized):
            return True

        if cls.looks_like_prev_page_request(normalized):
            return True

        return cls.looks_like_more_results_request(normalized)

    @classmethod
    def looks_like_next_page_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            cls._NEXT_PAGE_TERMS,
        )

    @classmethod
    def looks_like_prev_page_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            cls._PREV_PAGE_TERMS,
        )

    @classmethod
    def looks_like_more_results_request(cls, normalized: str) -> bool:
        return ChatMessageNormalizationService.contains_any(
            normalized,
            cls._MORE_RESULTS_TERMS,
        )

    @classmethod
    def looks_like_depth_increase_request(cls, normalized: str) -> bool:
        if cls.extract_requested_max_depth(normalized) is not None:
            return True

        return ChatMessageNormalizationService.contains_any(
            normalized,
            cls._DEPTH_INCREASE_TERMS,
        )

    @classmethod
    def extract_requested_max_depth(cls, normalized: str) -> int | None:
        match = cls._MAX_DEPTH_RE.search(normalized)

        if not match:
            return None

        value = int(match.group(1))

        if 1 <= value <= 99:
            return value

        return None

    @classmethod
    def _is_operational_navigation_message(cls, normalized: str) -> bool:
        return (
            cls.looks_like_pagination_request(normalized)
            or cls.looks_like_depth_increase_request(normalized)
        )

    @classmethod
    def extract_requested_page_size(cls, normalized: str) -> int | None:
        for pattern in cls._PAGE_SIZE_PATTERNS:
            match = pattern.search(normalized)

            if not match:
                continue

            value = int(match.group(1))

            if 1 <= value <= 500:
                return value

        return None

    @classmethod
    def extract_requested_page(cls, normalized: str) -> int | None:
        match = cls._PAGE_NUMBER_RE.search(normalized)

        if not match:
            return None

        value = int(match.group(1))

        if value >= 1:
            return value

        return None

    @classmethod
    def collect_recent_paginated_action(
        cls,
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
    def _collect_recent_paginated_action_from_tool_calls(
        cls,
        previous_messages: list[Any] | None,
    ) -> RecentPaginatedAction | None:
        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(cls._message_metadata(item).get("toolCalls") or []):
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

                if not cls._has_paginated_coverage(coverage) and not cls._is_paginated_path(
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

                product_code = cls._parameter_str(parameters, "code")
                route_segment = cls._route_segment_from_path(path)
                page, page_size = cls._resolve_pagination_state(
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
    def _collect_recent_paginated_action_from_context(
        cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> RecentPaginatedAction | None:
        product_code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
            previous_messages or [],
        )

        if not product_code:
            return None

        route_segment = cls._infer_paginated_route_segment(
            previous_messages,
            conversation_context=conversation_context,
        )

        if not route_segment:
            return None

        snapshot = cls._extract_latest_operational_snapshot(
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
            page=page or cls._parameter_int(parameters, "page") or 1,
            page_size=page_size or cls._parameter_int(parameters, "page_size") or 25,
            product_code=product_code,
            route_segment=route_segment,
        )

    @classmethod
    def _extract_latest_operational_snapshot(
        cls,
        previous_messages: list[Any] | None,
        *,
        conversation_context: str | None = None,
    ) -> dict[str, Any] | None:
        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(cls._message_metadata(item).get("toolCalls") or []):
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
                    for fragment in cls._PAGINATED_PATH_FRAGMENTS
                ):
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                coverage = tool_meta.get("dataCoverageNotice")
                page, page_size = cls._resolve_pagination_state(
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

        for fragment in cls._PAGINATED_PATH_FRAGMENTS:
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

        return any(fragment in lowered for fragment in cls._PAGINATED_PATH_FRAGMENTS)

    @classmethod
    def _resolve_page_size_from_parameters(cls, parameters: dict) -> int | None:
        for key in ("page_size", "pagesize", "limit"):
            value = cls._parameter_int(parameters, key)

            if value is not None:
                return value

        return None

    @classmethod
    def _resolve_pagination_state(
        cls,
        parameters: dict,
        coverage: dict | None,
    ) -> tuple[int | None, int | None]:
        page = cls._parameter_int(parameters, "page")
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
    def _infer_paginated_route_segment(
        cls,
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
            for tool_call in reversed(cls._message_metadata(item).get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                route_segment = cls._route_segment_from_path(str(tool_meta.get("path") or ""))

                if route_segment:
                    return route_segment

        for item in reversed((previous_messages or [])[-14:]):
            if cls._message_field_role(item) != "user":
                continue

            normalized = ChatMessageNormalizationService.normalize_for_matching(
                cls._message_content(item),
            )

            if cls._is_operational_navigation_message(normalized):
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

    @classmethod
    def _message_field_role(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @classmethod
    def _parameter_str(cls, parameters: dict, key: str) -> str | None:
        for name, value in parameters.items():
            if str(name).lower() != key.lower():
                continue

            raw = str(value or "").strip()

            if raw:
                return raw

        return None

    @classmethod
    def _parameter_int(cls, parameters: dict, key: str) -> int | None:
        for name, value in parameters.items():
            if str(name).lower() != key.lower():
                continue

            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return None

    @classmethod
    def plan_metric_follow_ups(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = ChatRouteContextService.collect_recent_metric_route(previous_messages)

        if not recent:
            return []

        branch = cls.extract_branch_code(normalized)

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

        if not cls.looks_like_operational_refinement(normalized):
            return []

        if not branch and not cls._requires_stock_refinement(normalized):
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

    @classmethod
    def plan_stock_follow_ups(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not cls._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return []

        product_codes = cls._collect_recent_stock_product_codes(previous_messages)

        if not product_codes:
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
            )

            if code:
                product_codes = [code]

        if not product_codes:
            return []

        if cls.looks_like_stock_scope_reset(normalized):
            return [
                OperationalRefinement(
                    kind="stock_reset",
                    product_code=code,
                    reason=(
                        "A mensagem pede o estoque completo novamente, sem filtro de filial."
                    ),
                )
                for code in product_codes
            ]

        if not cls.looks_like_operational_refinement(normalized):
            return []

        branch = cls.extract_branch_code(normalized)
        warehouse = cls.extract_warehouse_code(normalized)

        if not branch and not warehouse and not cls._requires_stock_refinement(normalized):
            return []

        return [
            OperationalRefinement(
                kind="stock_refinement",
                product_code=code,
                branch=branch,
                warehouse=warehouse,
                reason="A mensagem refina a consulta de estoque já feita nesta conversa.",
            )
            for code in product_codes
        ]

    @classmethod
    def detect(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalRefinement | None:
        planned = cls.plan_operational_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not planned:
            return None

        return planned[0]

    @classmethod
    def looks_like_operational_refinement(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._FILTER_TERMS):
            return True

        if "filial" in normalized and any(
            term in normalized
            for term in ("filtre", "filtro", "filtrar", "só", "so", "apenas", "somente")
        ):
            return True

        if cls.extract_branch_code(normalized):
            return True

        if cls.extract_warehouse_code(normalized):
            return True

        return False

    @classmethod
    def is_operational_follow_up(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if cls.plan_operational_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        branch = cls.extract_branch_code(normalized)
        warehouse = cls.extract_warehouse_code(normalized)

        if branch or warehouse:
            if ChatRouteContextService.collect_recent_metric_route(previous_messages):
                return True

            if cls._has_recent_stock_context(
                conversation_context=conversation_context,
                previous_messages=previous_messages,
            ):
                return True

        if not ChatProductQueryIntentService.references_previous_product(message):
            return False

        if cls._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        if ChatRouteContextService.collect_recent_metric_route(previous_messages):
            return True

        return bool(
            ChatRouteContextService.collect_recent_product_route_batch(previous_messages)
        )

    @classmethod
    def extract_branch_code(cls, normalized: str) -> str | None:
        match = cls._BRANCH_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def extract_warehouse_code(cls, normalized: str) -> str | None:
        match = cls._WAREHOUSE_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def _requires_stock_refinement(cls, normalized: str) -> bool:
        return "filial" in normalized or "armazem" in normalized or "armazém" in normalized

    @classmethod
    def _has_recent_stock_context(
        cls,
        *,
        conversation_context: str | None,
        previous_messages: list[Any] | None,
    ) -> bool:
        if conversation_context:
            lowered = conversation_context.lower()

            if "/stock" in lowered or "estoque do produto" in lowered:
                return True

        for item in reversed((previous_messages or [])[-10:]):
            metadata = cls._message_metadata(item)

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()

                if "/stock" in path or "product_stock" in action_id or "get_product_stock" in action_id:
                    return True

            content = cls._message_content(item).lower()

            if "estoque do produto" in content or "estoque por filial" in content:
                return True

        return False

    @classmethod
    def _collect_recent_stock_product_codes(
        cls,
        previous_messages: list[Any] | None,
    ) -> list[str]:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-14:]):
            batch_codes: list[str] = []

            for tool_call in cls._message_metadata(item).get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()

                if "/stock" not in path and "product_stock" not in action_id:
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

                if not code:
                    arguments = tool_call.get("arguments") or {}
                    parameters = arguments.get("parameters") or {}

                    if isinstance(parameters, dict):
                        for key in (
                            "code",
                            "product_code",
                            "productcode",
                            "codigo",
                            "cod_produto",
                        ):
                            raw = parameters.get(key)

                            if not raw:
                                continue

                            candidate = ChatProductQueryIntentService.normalize_product_code(
                                str(raw)
                            )

                            if candidate and not ChatAnalysisIntentService.looks_like_path_placeholder(
                                candidate
                            ):
                                code = candidate
                                break

                if code and code not in batch_codes:
                    batch_codes.append(code)

            if batch_codes:
                return batch_codes

        return []

    @classmethod
    def _product_code_from_messages(cls, previous_messages: list[Any]) -> str | None:
        for item in reversed(previous_messages[-12:]):
            code = ChatProductQueryIntentService.extract_product_code(
                cls._message_content(item)
            )

            if code:
                return code

        return None

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _message_content(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")
