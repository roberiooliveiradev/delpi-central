"""Planejamento de várias rotas /products/{code}/… na mesma pergunta."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)

# Ordem estável de execução quando são necessárias rotas separadas.
_SCOPE_FETCH_ORDER: tuple[str, ...] = (
    "profile",
    "guide",
    "inspection",
    "structure",
    "stock",
    "open_orders",
    "parents",
    "sales",
    "purchases",
    "suppliers",
    "pricing",
    "inbound_invoice",
    "outbound_invoice",
)

_SCOPE_TO_ROUTE: dict[str, tuple[str, str | None]] = {
    "profile": (ChatProductQueryIntent.DESCRIPTION, None),
    "guide": (ChatProductQueryIntent.FULL, "guide"),
    "inspection": (ChatProductQueryIntent.FULL, "inspection"),
    "structure": (ChatProductQueryIntent.STRUCTURE, "structure"),
    "stock": (ChatProductQueryIntent.STOCK, "stock"),
    "open_orders": (ChatProductQueryIntent.FULL, "open-orders"),
    "parents": (ChatProductQueryIntent.PARENTS, "parents"),
    "sales": (ChatProductQueryIntent.SALES, "sales"),
    "purchases": (ChatProductQueryIntent.FULL, "purchases"),
    "suppliers": (ChatProductQueryIntent.FULL, "suppliers"),
    "pricing": (ChatProductQueryIntent.FULL, "pricing"),
    "inbound_invoice": (ChatProductQueryIntent.FULL, "inbound-invoice"),
    "outbound_invoice": (ChatProductQueryIntent.FULL, "outbound-invoice"),
}

_FALLBACK_EXPLICIT_ANALYSER_TERMS: tuple[str, ...] = (
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
    def analyser_bundle_scopes(cls) -> frozenset[str]:
        return ChatProductQueryIntentContentService.analyser_bundle_scopes()

    @classmethod
    def companion_scopes_allowed(cls) -> frozenset[str]:
        return ChatProductQueryIntentContentService.companion_scopes_allowed()

    @classmethod
    def _explicit_analyser_terms(cls) -> tuple[str, ...]:
        configured = ChatProductQueryIntentContentService.explicit_analyser_terms()
        return configured or _FALLBACK_EXPLICIT_ANALYSER_TERMS

    @classmethod
    def extract_requested_scopes(cls, message: str | None) -> tuple[str, ...]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return ()

        if cls._is_dedicated_playbook_route_question(normalized):
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
                "descricao",
                "descrição",
                "description",
            )
        ):
            add("profile")

        if any(term in normalized for term in ("roteiro", "roteiros")):
            add("guide")

        if any(
            term in normalized
            for term in (
                "inspeção",
                "inspecao",
                "inspeções",
                "inspecoes",
            )
        ):
            add("inspection")

        if any(
            term in normalized
            for term in (
                "estrutura",
                "estruturas",
                "bom",
                "composição",
                "composicao",
                "composições",
                "composicoes",
            )
        ):
            add("structure")

        stock_terms = ChatProductQueryIntentContentService.stock_terms() or (
            "estoque",
            "stock",
            "saldo",
            "quantidade dispon",
            "posição de estoque",
            "posicao de estoque",
            "tem em estoque",
            "qtd dispon",
        )
        if any(term in normalized for term in stock_terms):
            add("stock")

        open_orders_terms = ChatProductQueryIntentContentService.open_orders_terms()
        if open_orders_terms and any(term in normalized for term in open_orders_terms):
            add("open_orders")
        elif ChatProductQueryIntentService._looks_like_open_orders_route_question(normalized):
            add("open_orders")

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

        # NF só entra no multi-scope com direção explícita (entrada/saída).
        if any(
            term in normalized
            for term in (
                "nota de entrada",
                "notas de entrada",
                "notas fiscais de entrada",
                "nf de entrada",
                "inbound",
            )
        ):
            add("inbound_invoice")

        if any(
            term in normalized
            for term in (
                "nota de saída",
                "nota de saida",
                "notas de saída",
                "notas de saida",
                "notas fiscais de saída",
                "notas fiscais de saida",
                "nf de saída",
                "nf de saida",
                "outbound",
            )
        ):
            add("outbound_invoice")

        ordered = [scope for scope in _SCOPE_FETCH_ORDER if scope in found]

        return tuple(ordered)

    @classmethod
    def companion_scopes(cls, scopes: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        bundle = cls.analyser_bundle_scopes()
        allowed = cls.companion_scopes_allowed()
        ordered = [
            scope
            for scope in _SCOPE_FETCH_ORDER
            if scope in scopes and scope not in bundle and (not allowed or scope in allowed)
        ]
        return tuple(ordered)

    @classmethod
    def blocks_intent_bound_fast_path(cls, message: str | None) -> bool:
        """Companions fora do bundle analyser (ou multi-escopo) impedem short-circuit single-action."""
        scopes = cls.extract_requested_scopes(message)
        companions = cls.companion_scopes(scopes)

        if cls._has_explicit_analyser_phrase(message) and companions:
            return True

        if len(scopes) >= 2:
            return True

        return False

    @classmethod
    def is_exclusive_open_orders_or_sale_orders_list_turn(cls, message: str | None) -> bool:
        """Listagem de OV só é early-path quando não há outros escopos de produto."""
        scopes = cls.extract_requested_scopes(message)
        if not scopes:
            return True
        return all(scope == "open_orders" for scope in scopes)

    @classmethod
    def missing_scopes_for_planned_actions(
        cls,
        message: str | None,
        planned: list[dict] | None,
    ) -> tuple[str, ...]:
        """Escopos pedidos na mensagem que ainda não aparecem nos paths planejados."""
        requested = cls.extract_requested_scopes(message)
        if not requested:
            return ()

        haystack = cls._planned_action_haystack(planned)

        missing: list[str] = []
        for scope in requested:
            _intent, segment = _SCOPE_TO_ROUTE.get(scope, (None, None))
            markers = [m for m in (segment, scope.replace("_", "-"), scope) if m]
            if scope == "profile":
                markers.extend(["/products/{code}", "/analyser", "/summary", "/detail"])
                # Bare product detail path often ends with /products/{code} without segment.
            if any(marker and marker in haystack for marker in markers):
                continue
            # analyser cobre o bundle
            if scope in cls.analyser_bundle_scopes() and "/analyser" in haystack:
                continue
            missing.append(scope)

        return tuple(missing)

    @classmethod
    def _planned_action_haystack(cls, planned: list[dict] | None) -> str:
        """Path + actionId + operationId — planos OpenAPI-first nem sempre copiam path em arguments."""
        parts: list[str] = []
        for item in planned or []:
            if not isinstance(item, dict):
                continue
            args = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            parts.extend(
                [
                    str(args.get("path") or ""),
                    str(item.get("path") or ""),
                    str(meta.get("path") or ""),
                    str(args.get("actionId") or ""),
                    str(item.get("actionId") or ""),
                    str(meta.get("actionId") or ""),
                    str(meta.get("operationId") or ""),
                    str(args.get("operationId") or ""),
                ]
            )
        return " ".join(parts).lower()

    @classmethod
    def _is_dedicated_playbook_route_question(cls, normalized: str) -> bool:
        """Rotas playbook com path próprio não entram em multi-scope genérico."""
        dedicated_checks = (
            ChatProductQueryIntentService._looks_like_purchase_price_history_question,
            ChatProductQueryIntentService._looks_like_purchase_budget_history_question,
            ChatProductQueryIntentService._looks_like_last_purchase_question,
            ChatProductQueryIntentService._looks_like_raw_material_price_intelligence_question,
            ChatProductQueryIntentService._looks_like_cost_impact_simulation_question,
            ChatProductQueryIntentService._looks_like_sale_pricing_question,
        )

        return any(check(normalized) for check in dedicated_checks)

    @classmethod
    def should_use_single_analyser(cls, scopes: tuple[str, ...], message: str | None) -> bool:
        if cls._has_explicit_analyser_phrase(message):
            return True

        if not scopes:
            return False

        bundle = cls.analyser_bundle_scopes()
        analyser_scopes = tuple(scope for scope in scopes if scope in bundle)

        if not analyser_scopes:
            return False

        # Companions fora do bundle: ainda colapsa a parte analyser, se houver ≥ min.
        analyser_only = all(scope in bundle for scope in scopes)
        min_scopes = ChatProductQueryIntentContentService.min_analyser_scopes_for_collapse()

        if analyser_only:
            return len(analyser_scopes) >= min_scopes

        return len(analyser_scopes) >= min_scopes

    @classmethod
    def _has_explicit_analyser_phrase(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return any(term in normalized for term in cls._explicit_analyser_terms())

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

        companions = cls.companion_scopes(scopes)
        use_analyser = cls._has_explicit_analyser_phrase(message) or (
            scopes and cls.should_use_single_analyser(scopes, message)
        )

        if use_analyser:
            planned: list[dict] = []
            selected = selection_service.select_action_for_product(
                message,
                product_code=code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.ANALYSER,
                route_segment="analyser",
                previous_messages=previous_messages,
            )
            if selected:
                planned.append(selected)
            else:
                # Sem action analyser: expande o bundle em rotas individuais.
                bundle = cls.analyser_bundle_scopes()
                for scope in scopes:
                    if scope not in bundle:
                        continue
                    if len(planned) >= max(1, min(int(max_calls), 12)):
                        break
                    expanded = cls._select_scope_action(
                        selection_service,
                        message=message,
                        product_code=code,
                        scope=scope,
                        allowed_action_ids=allowed_action_ids,
                        previous_messages=previous_messages,
                    )
                    if expanded:
                        planned.append(expanded)

            limit = max(1, min(int(max_calls), 12))
            for scope in companions:
                if len(planned) >= limit:
                    break
                companion = cls._select_scope_action(
                    selection_service,
                    message=message,
                    product_code=code,
                    scope=scope,
                    allowed_action_ids=allowed_action_ids,
                    previous_messages=previous_messages,
                )
                if companion:
                    planned.append(companion)

            return planned

        if len(scopes) < 2:
            return []

        limit = max(1, min(int(max_calls), 12))
        planned = []

        for scope in scopes:
            if len(planned) >= limit:
                break

            selected = cls._select_scope_action(
                selection_service,
                message=message,
                product_code=code,
                scope=scope,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
            )
            if selected:
                planned.append(selected)

        return planned

    @classmethod
    def _select_scope_action(
        cls,
        selection_service: Any,
        *,
        message: str,
        product_code: str,
        scope: str,
        allowed_action_ids: list[str] | None,
        previous_messages: list | None,
    ) -> dict | None:
        intent, route_segment = _SCOPE_TO_ROUTE.get(scope, (ChatProductQueryIntent.FULL, None))

        selected = selection_service.select_action_for_product(
            message,
            product_code=product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            previous_messages=previous_messages,
        )

        if not selected:
            return None

        selected = dict(selected)
        selected["reason"] = cls._reason_for_scope(scope, product_code)
        return selected

    @classmethod
    def _reason_for_scope(cls, scope: str, product_code: str) -> str:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        label = ChatProductOperationalContentService.scope_label_for_scope_key(scope)

        return ChatProductOperationalContentService.format(
            "multiScope",
            "reasonTemplate",
            scope=label,
            code=product_code,
        )
