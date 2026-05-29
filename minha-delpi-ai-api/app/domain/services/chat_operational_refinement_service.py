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
    )
    _NEXT_PAGE_TERMS = (
        "proxima pagina",
        "próxima página",
        "proxima pag",
        "seguinte pagina",
        "seguinte página",
        "pagina seguinte",
        "página seguinte",
        "next page",
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
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = cls.collect_recent_paginated_action(previous_messages)

        if not recent or not cls.looks_like_pagination_request(normalized):
            return []

        page_size = cls.extract_requested_page_size(normalized)
        page = cls.extract_requested_page(normalized)

        if page is None and cls.looks_like_next_page_request(normalized):
            current_page = recent.page or cls._parameter_int(recent.parameters, "page") or 1
            page = current_page + 1

        if page is None and page_size is None and cls.looks_like_more_results_request(normalized):
            current_page = recent.page or cls._parameter_int(recent.parameters, "page") or 1
            page = current_page + 1

        if page is None and page_size is None:
            return []

        return [
            OperationalRefinement(
                kind="pagination_refinement",
                action_id=recent.action_id,
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
    def looks_like_pagination_request(cls, normalized: str) -> bool:
        if cls.extract_requested_page_size(normalized) is not None:
            return True

        if cls.extract_requested_page(normalized) is not None:
            return True

        if cls.looks_like_next_page_request(normalized):
            return True

        return cls.looks_like_more_results_request(normalized)

    @classmethod
    def looks_like_next_page_request(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._NEXT_PAGE_TERMS)

    @classmethod
    def looks_like_more_results_request(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._MORE_RESULTS_TERMS)

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

                has_pagination_notice = (
                    isinstance(coverage, dict)
                    and str(coverage.get("kind") or "").lower() == "pagination"
                )

                if not has_pagination_notice and not any(
                    fragment in lowered_path for fragment in cls._PAGINATED_PATH_FRAGMENTS
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

                if not action_id:
                    continue

                return RecentPaginatedAction(
                    action_id=action_id,
                    path=path,
                    parameters=dict(parameters),
                    page=cls._parameter_int(parameters, "page"),
                    page_size=cls._parameter_int(parameters, "page_size"),
                )

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
