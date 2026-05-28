"""Contexto de rotas OpenAPI recentes — herança multi-turno entre domínios."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


@dataclass(frozen=True)
class RecentMetricRoute:
    """Última consulta agregada (KPI departamental ou suprimentos)."""

    kind: str
    domain_prefix: str
    path_token: str
    path: str
    reason: str = ""


@dataclass(frozen=True)
class RecentProductRouteBatch:
    """Lote recente de consultas /products/{code}/… na mesma resposta."""

    product_codes: tuple[str, ...]
    route_segment: str


class ChatRouteContextService:
    """Mapeia segmentos de path e histórico de tools para herança de intenção."""

    _PRODUCT_SEGMENT_TO_INTENT: dict[str, str] = {
        "stock": ChatProductQueryIntent.STOCK,
        "summary": ChatProductQueryIntent.SUMMARY,
        "analyser": ChatProductQueryIntent.ANALYSER,
        "structure": ChatProductQueryIntent.STRUCTURE,
        "parents": ChatProductQueryIntent.PARENTS,
    }

    _PRODUCT_ROUTE_SEGMENTS: frozenset[str] = frozenset(
        {
            "purchases",
            "suppliers",
            "sales",
            "pricing",
            "guide",
            "inspection",
            "internal-movements",
            "inbound-invoice",
            "outbound-invoice",
            "customers",
        }
    )

    _MESSAGE_SEGMENT_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("purchases", ("ultima compra", "últimas compras", "ultimas compras", "compra", "purchase")),
        ("suppliers", ("fornecedor", "fornecedore", "supplier")),
        ("sales", ("venda do produto", "vendas do produto", "historico de venda")),
        ("pricing", ("preço", "preco", "pricing", "quanto custa", "tabela de preço", "tabela de preco")),
        ("guide", ("roteiro", "guide", "rota de fabricação", "rota de fabricacao")),
        ("inspection", ("inspeção", "inspecao", "inspection")),
        ("internal-movements", ("movimentaç", "movimentac", "internal-movement")),
        ("inbound-invoice", ("nota de entrada", "notas de entrada", "inbound")),
        ("outbound-invoice", ("nota de saída", "nota de saida", "notas de saída", "notas de saida", "outbound")),
        ("customers", ("cliente do produto", "clientes do produto", "customer")),
    )

    _DEPARTMENT_DOMAIN_MARKERS: tuple[str, ...] = (
        "/commercial/",
        "/financial/",
        "/production/",
        "/hr/",
        "/quality/",
    )

    _SUPPLIES_DOMAIN_MARKERS: tuple[str, ...] = (
        "/supplies/",
    )

    _METRIC_SCOPE_RESET_TERMS: tuple[str, ...] = (
        "sem filtro",
        "sem filial",
        "todas as filiais",
        "todas filiais",
        "remova o filtro",
        "remover filtro",
        "tire o filtro",
        "visao completa",
        "visão completa",
        "completo de novo",
        "tudo de novo",
    )

    _PRODUCT_FOLLOWUP_TERMS: tuple[str, ...] = (
        "ultimas compras",
        "últimas compras",
        "ultima compra",
        "última compra",
        "fornecedores",
        "fornecedor",
        "notas de entrada",
        "notas de saída",
        "notas de saida",
        "roteiro",
        "movimentação",
        "movimentacao",
        "inspeção",
        "inspecao",
        "e o estoque",
        "e as compras",
        "e as vendas",
        "e os fornecedores",
    )

    @classmethod
    def intent_for_product_segment(cls, segment: str | None) -> str | None:
        if not segment:
            return None

        key = str(segment).strip().lower()

        return cls._PRODUCT_SEGMENT_TO_INTENT.get(key)

    @classmethod
    def is_product_route_segment(cls, segment: str | None) -> bool:
        if not segment:
            return False

        return str(segment).strip().lower() in cls._PRODUCT_ROUTE_SEGMENTS

    @classmethod
    def segment_from_message(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        for segment, terms in cls._MESSAGE_SEGMENT_HINTS:
            if any(term in normalized for term in terms):
                return segment

        return None

    @classmethod
    def infer_product_route_segment_from_recent_tool(
        cls,
        previous_messages: list | None,
    ) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                segment = ChatAnalysisIntentService.extract_product_path_segment(
                    str(tool_meta.get("path") or "")
                )

                if segment and (
                    segment in cls._PRODUCT_SEGMENT_TO_INTENT
                    or segment in cls._PRODUCT_ROUTE_SEGMENTS
                ):
                    return segment

        return None

    @classmethod
    def resolve_product_route_segment(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> str | None:
        explicit = cls.segment_from_message(message)

        if explicit:
            return explicit

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._looks_like_product_route_followup(normalized):
            return cls.infer_product_route_segment_from_recent_tool(previous_messages)

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if ChatProductQueryIntentService.references_previous_product(message):
            return cls.infer_product_route_segment_from_recent_tool(previous_messages)

        return None

    @classmethod
    def collect_recent_product_route_batch(
        cls,
        previous_messages: list | None,
        *,
        route_segment: str | None = None,
    ) -> RecentProductRouteBatch | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        segment_filter = str(route_segment or "").strip().lower() or None

        for item in reversed((previous_messages or [])[-14:]):
            batch_codes: list[str] = []
            batch_segment: str | None = None

            for tool_call in cls._message_metadata(item).get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")
                segment = ChatAnalysisIntentService.extract_product_path_segment(path)

                if not segment:
                    continue

                if segment_filter and segment != segment_filter:
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

                if not code:
                    continue

                batch_segment = segment

                if code not in batch_codes:
                    batch_codes.append(code)

            if batch_codes and batch_segment:
                return RecentProductRouteBatch(
                    product_codes=tuple(batch_codes),
                    route_segment=batch_segment,
                )

        return None

    @classmethod
    def collect_recent_metric_route(
        cls,
        previous_messages: list | None,
    ) -> RecentMetricRoute | None:
        for item in reversed((previous_messages or [])[-12:]):
            for tool_call in reversed(cls._message_metadata(item).get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()

                if "/products/" in path:
                    continue

                if any(marker in path for marker in cls._SUPPLIES_DOMAIN_MARKERS):
                    token = cls._extract_path_token(path, cls._SUPPLIES_DOMAIN_MARKERS)

                    if token:
                        return RecentMetricRoute(
                            kind="supplies",
                            domain_prefix="/supplies/",
                            path_token=token,
                            path=path,
                            reason="Refino da consulta de suprimentos já feita nesta conversa.",
                        )

                if any(marker in path for marker in cls._DEPARTMENT_DOMAIN_MARKERS):
                    domain = next(
                        marker
                        for marker in cls._DEPARTMENT_DOMAIN_MARKERS
                        if marker in path
                    )
                    token = cls._extract_path_token(path, (domain,))

                    if token:
                        return RecentMetricRoute(
                            kind="department_kpi",
                            domain_prefix=domain,
                            path_token=token,
                            path=path,
                            reason="Refino do KPI departamental já consultado nesta conversa.",
                        )

        return None

    @classmethod
    def looks_like_metric_scope_reset(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._METRIC_SCOPE_RESET_TERMS)

    @classmethod
    def _looks_like_product_route_followup(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._PRODUCT_FOLLOWUP_TERMS)

    @classmethod
    def _extract_path_token(cls, path: str, domain_markers: tuple[str, ...]) -> str | None:
        lowered = path.lower().strip("/")
        parts = [part for part in lowered.split("/") if part]

        if len(parts) < 2:
            return None

        domain = parts[0]

        if not any(domain in marker.strip("/") for marker in domain_markers):
            return None

        token = parts[1]

        if token in {"series", "search"} and len(parts) >= 3:
            return f"{token}/{parts[2]}"

        return token

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
