"""Planejamento de várias rotas /products/{code}/… na mesma pergunta."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)

# Escopos cobertos por GET /products/{code}/analyser (cadastro + guia + inspeção + BOM).
_ANALYSER_SCOPES: frozenset[str] = frozenset(
    {"profile", "guide", "structure", "inspection"},
)

# Ordem estável de execução quando são necessárias rotas separadas.
_SCOPE_FETCH_ORDER: tuple[str, ...] = (
    "profile",
    "guide",
    "inspection",
    "structure",
    "stock",
    "parents",
    "sales",
    "purchases",
    "suppliers",
    "pricing",
)

_SCOPE_TO_ROUTE: dict[str, tuple[str, str | None]] = {
    "profile": (ChatProductQueryIntent.DESCRIPTION, None),
    "guide": (ChatProductQueryIntent.FULL, "guide"),
    "inspection": (ChatProductQueryIntent.FULL, "inspection"),
    "structure": (ChatProductQueryIntent.STRUCTURE, "structure"),
    "stock": (ChatProductQueryIntent.STOCK, "stock"),
    "parents": (ChatProductQueryIntent.PARENTS, "parents"),
    "sales": (ChatProductQueryIntent.SALES, "sales"),
    "purchases": (ChatProductQueryIntent.FULL, "purchases"),
    "suppliers": (ChatProductQueryIntent.FULL, "suppliers"),
    "pricing": (ChatProductQueryIntent.FULL, "pricing"),
}

_EXPLICIT_ANALYSER_TERMS: tuple[str, ...] = (
    "ficha completa",
    "analise completa",
    "análise completa",
    "analise integrada",
    "análise integrada",
    "visao integrada",
    "visão integrada",
    "analisador completo",
    "analisador do produto",
    "informacoes completas",
    "informações completas",
    "tudo sobre o produto",
)


class ChatProductMultiScopePlanningService:
    @classmethod
    def extract_requested_scopes(cls, message: str | None) -> tuple[str, ...]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return ()

        found: list[str] = []

        def add(scope: str) -> None:
            if scope not in found:
                found.append(scope)

        if any(
            term in normalized
            for term in (
                "cadastro",
                "ficha",
                "dados cadastrais",
                "informacoes do produto",
                "informações do produto",
                "dados do produto",
            )
        ):
            add("profile")

        if "roteiro" in normalized:
            add("guide")

        if any(term in normalized for term in ("inspeção", "inspecao", "inspeções", "inspecoes")):
            add("inspection")

        if any(term in normalized for term in ("estrutura", "bom", "composição", "composicao")):
            add("structure")

        if any(
            term in normalized
            for term in (
                "estoque",
                "stock",
                "saldo",
                "disponível",
                "disponivel",
            )
        ):
            add("stock")

        if ChatProductQueryIntentService._looks_like_parents_question(normalized):
            add("parents")

        if ChatProductQueryIntentService._looks_like_sales_question(normalized):
            add("sales")

        if any(term in normalized for term in ("compra", "compras", "purchase")):
            add("purchases")

        if any(term in normalized for term in ("fornecedor", "fornecedore", "supplier")):
            add("suppliers")

        if any(
            term in normalized
            for term in ("preço", "preco", "pricing", "quanto custa", "tabela de preço", "tabela de preco")
        ):
            add("pricing")

        ordered = [scope for scope in _SCOPE_FETCH_ORDER if scope in found]

        return tuple(ordered)

    @classmethod
    def should_use_single_analyser(cls, scopes: tuple[str, ...], message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if any(term in normalized for term in _EXPLICIT_ANALYSER_TERMS):
            return True

        if not scopes:
            return False

        analyser_only = all(scope in _ANALYSER_SCOPES for scope in scopes)

        if not analyser_only:
            return False

        return len(scopes) >= 3

    @classmethod
    def _has_explicit_analyser_phrase(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return any(term in normalized for term in _EXPLICIT_ANALYSER_TERMS)

    @classmethod
    def plan_product_scope_fetches(
        cls,
        selection_service: Any,
        *,
        message: str,
        product_code: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None = None,
        max_calls: int = 6,
    ) -> list[dict]:
        scopes = cls.extract_requested_scopes(message)
        code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not code:
            return []

        if cls._has_explicit_analyser_phrase(message) or (
            scopes and cls.should_use_single_analyser(scopes, message)
        ):
            selected = selection_service.select_action_for_product(
                message,
                product_code=code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.ANALYSER,
                previous_messages=previous_messages,
            )

            return [selected] if selected else []

        if len(scopes) < 2:
            return []

        limit = max(1, min(int(max_calls), 12))
        planned: list[dict] = []

        for scope in scopes:
            if len(planned) >= limit:
                break

            intent, route_segment = _SCOPE_TO_ROUTE.get(scope, (ChatProductQueryIntent.FULL, None))

            selected = selection_service.select_action_for_product(
                message,
                product_code=code,
                allowed_action_ids=allowed_action_ids,
                intent=intent,
                route_segment=route_segment,
                previous_messages=previous_messages,
            )

            if not selected:
                continue

            selected = dict(selected)
            selected["reason"] = cls._reason_for_scope(scope, code)
            planned.append(selected)

        return planned

    @classmethod
    def _reason_for_scope(cls, scope: str, product_code: str) -> str:
        labels = {
            "profile": "cadastro",
            "guide": "roteiro de produção",
            "inspection": "plano de inspeção",
            "structure": "estrutura (BOM)",
            "stock": "estoque",
            "parents": "produtos pai",
            "sales": "vendas",
            "purchases": "compras",
            "suppliers": "fornecedores",
            "pricing": "preços",
        }
        label = labels.get(scope, scope)

        return (
            f"A pergunta pede {label} do produto {product_code} "
            "(consulta combinada com outras rotas na mesma mensagem)."
        )
