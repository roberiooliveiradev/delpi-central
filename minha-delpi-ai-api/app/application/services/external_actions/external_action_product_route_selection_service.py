"""Seleção de actions OpenAPI de produto — Fase 3B lote 4."""

from __future__ import annotations

import re
from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class ExternalActionProductRouteSelectionService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15

    def __init__(self, repository) -> None:
        self.repository = repository

    def _load_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable | None = None,
    ) -> list[dict]:
        candidates: list[dict] = []

        if allowed_action_ids and candidates_loader:
            candidates = candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )

        if not candidates:
            candidates = self.repository.find_candidate_actions(
                message,
                limit=80,
            )

        return candidates or []

    def select(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
        candidates_loader: Callable | None = None,
    ) -> dict | None:
        candidates = self._load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

        if not candidates:
            return None

        candidates = [
            action
            for action in candidates
            if action.get("method") == "GET"
        ] or candidates

        invoice_segment = str(route_segment or "").strip().lower()
        if invoice_segment in ("outbound-invoice", "inbound-invoice"):
            invoice_candidates = [
                action
                for action in candidates
                if f"/{invoice_segment}" in str(action.get("path") or "").lower()
            ]

            if invoice_candidates:
                candidates = invoice_candidates
            else:
                return None
        elif intent == ChatProductQueryIntent.SALES:
            sales_candidates = [
                action
                for action in candidates
                if self._is_product_sales_summary_path(str(action.get("path") or ""))
            ]

            if not sales_candidates:
                return None

            candidates = sales_candidates
        else:
            candidates = [
                action
                for action in candidates
                if "search" not in str(action.get("path") or "").lower()
            ] or candidates

        ranked = self._rank_product_actions(
            candidates,
            intent=intent,
            message=message,
            route_segment=route_segment,
        )

        if preferred_action_id:
            preferred = next(
                (
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") == preferred_action_id
                ),
                None,
            )

            if preferred:
                ranked = [preferred, *[
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") != preferred_action_id
                ]]

        for action in ranked:
            parameters = self._build_product_parameters(
                action,
                product_code,
                message=message,
            )

            if parameters:
                reason = "A pergunta solicita informações operacionais de produto via OpenAPI."

                if branch_code := (
                    ChatOperationalRefinementService.extract_branch_code(
                        ChatMessageNormalizationService.normalize_for_matching(message)
                    )
                ):
                    reason = (
                        f"A mensagem refina o estoque do produto {product_code} "
                        f"para a filial {branch_code}."
                    )

                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": action["actionId"],
                        "parameters": parameters,
                    },
                    "reason": reason,
                }

        return None

    def _rank_product_actions(
        self,
        candidates: list[dict],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        message: str | None = None,
        route_segment: str | None = None,
    ) -> list[dict]:
        normalized = str(message or "").lower()
        inherited_segment = str(route_segment or "").strip().lower()
        wants_purchases = any(
            term in normalized
            for term in (
                "compra",
                "compras",
                "ultimas compras",
                "últimas compras",
                "ultima compra",
                "última compra",
                "fornecedor comprou",
                "histórico de compra",
                "historico de compra",
            )
        )
        wants_billing = ChatProductQueryIntentService._looks_like_billing_question(
            normalized
        )
        wants_factory_status = (
            ChatProductQueryIntentService._looks_like_factory_status_question(
                normalized
            )
        )
        wants_open_orders = any(
            term in normalized
            for term in ("carteira", "pedidos em aberto", "pedido em aberto", "open-orders")
        )
        wants_sales = (
            any(term in normalized for term in ("venda", "vendas"))
            or ("faturamento" in normalized and not wants_billing)
        ) and not wants_open_orders
        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        wants_product_overview = ChatProductOverviewIntentService.is_product_overview_message(
            message
        )
        wants_product_summary = wants_product_overview or any(
            term in normalized
            for term in (
                "resumo do produto",
                "resumo sintetico",
                "resumo sintético",
                "visao resumida",
                "visão resumida",
            )
        ) or (
            "resumo" in normalized
            and "completo" not in normalized
            and "ficha" not in normalized
            and "kaizen" not in normalized
        )
        wants_full_analyser = ChatProductQueryIntentService._looks_like_full_analyser_question(
            normalized
        )
        wants_structure = any(
            term in normalized
            for term in ("estrutura", "bom", "bill of material", "composição", "composicao")
        )
        wants_stock = any(
            term in normalized
            for term in ("estoque", "saldo", "disponível", "disponivel", "armazém", "armazem")
        ) and not wants_full_analyser

        wants_guide = any(
            term in normalized
            for term in ("roteiro", "guide", "rota de fabricação", "rota de fabricacao")
        )
        wants_suppliers = any(
            term in normalized
            for term in ("fornecedor", "fornecedore", "fornece", "supplier")
        ) or bool(re.search(r"\bfornece\b", normalized))
        wants_pricing = any(
            term in normalized
            for term in ("preço", "preco", "pricing", "tabela de preço", "tabela de preco", "quanto custa", "custo do")
        )
        wants_customers = any(
            term in normalized
            for term in ("cliente", "customer")
        )
        wants_parents = any(
            term in normalized
            for term in (
                "produto pai", "produtos pai", "parent", "where used",
                "onde é usado", "onde e usado", "pai do", "pais do",
                "quais produtos usam", "quais itens usam", "produtos que usam",
            )
        )
        wants_movements = any(
            term in normalized
            for term in ("movimentaç", "movimentac", "internal-movement")
        )
        wants_invoices = any(
            term in normalized
            for term in (
                "nota fiscal", "notas fiscai", "nfe", "invoice",
                "nota de entrada", "notas de entrada", "nota de saída", "nota de saida",
                "notas de saída", "notas de saida",
            )
        )
        wants_inbound = any(
            term in normalized for term in ("entrada", "inbound", "recebimento")
        )
        wants_outbound = any(
            term in normalized for term in ("saída", "saida", "outbound", "expedição", "expedicao")
        )
        wants_inspection = any(
            term in normalized
            for term in ("inspeção", "inspecao", "inspection", "qualidade")
        )

        if inherited_segment == "purchases":
            wants_purchases = True
        elif inherited_segment == "suppliers":
            wants_suppliers = True
        elif inherited_segment == "sales":
            wants_sales = True
        elif inherited_segment == "pricing":
            wants_pricing = True
        elif inherited_segment == "guide":
            wants_guide = True
        elif inherited_segment == "customers":
            wants_customers = True
        elif inherited_segment == "internal-movements":
            wants_movements = True
        elif inherited_segment == "inspection":
            wants_inspection = True
        elif inherited_segment == "inbound-invoice":
            wants_invoices = True
            wants_inbound = True
        elif inherited_segment == "outbound-invoice":
            wants_invoices = True
            wants_outbound = True

        has_specific_sub_intent = (
            wants_purchases or wants_sales or wants_open_orders or wants_structure
            or wants_guide or wants_suppliers or wants_pricing or wants_customers
            or wants_parents or wants_movements or wants_invoices or wants_inspection
            or wants_billing
            or wants_factory_status
            or wants_product_summary
            or wants_product_overview
            or wants_full_analyser
        )

        def score(action: dict) -> int:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()
            path = str(action.get("path") or "").lower()

            value = 0

            if wants_purchases and "/purchases" in path:
                value += 110

            if wants_billing and "/sales/billing" in path:
                value += 125

            if wants_factory_status and "factory-status" in path:
                value += 140

            if wants_open_orders and "open-orders" in path:
                value += 115

            elif wants_sales and self._is_product_sales_summary_path(path):
                value += 220

            elif wants_sales and "/sales" in path and "open-orders" not in path and "billing" not in path:
                value += 100

            if wants_product_overview and "/products/{code}/analyser" in haystack:
                value += 200

            if wants_product_overview and path.endswith("/analyser"):
                value += 180

            if wants_product_summary and "/summary" in path:
                value += 125

            if wants_product_overview and "/summary" in path:
                value += 160

            if wants_full_analyser and "analyser" in path:
                value += 125

            if wants_product_summary and not wants_product_overview and "analyser" in haystack:
                value -= 55

            if wants_product_overview and path.rstrip("/") == "/products/{code}":
                value += 40

            if wants_full_analyser and "/summary" in path:
                value -= 45

            if wants_structure and "/structure" in path:
                value += 120

            if wants_stock and (path.endswith("/stock") or "/products/{code}/stock" in haystack):
                value += 130

            if wants_stock and not wants_full_analyser and "analyser" in haystack:
                value -= 90

            if wants_structure and not wants_full_analyser and "analyser" in haystack:
                value -= 70

            if wants_guide and "/guide" in path:
                value += 120

            if wants_suppliers and "/suppliers" in path:
                value += 120

            if wants_pricing and "/pricing" in path:
                value += 120

            if wants_customers and "/customers" in path:
                value += 120

            if wants_parents and "/parents" in path:
                value += 120

            if wants_movements and "/internal-movements" in path:
                value += 120

            if wants_invoices:
                if wants_outbound and "/outbound-invoice" in path:
                    value += 130
                elif wants_inbound and "/inbound-invoice" in path:
                    value += 130
                elif "/inbound-invoice" in path or "/outbound-invoice" in path:
                    value += 120

            if wants_inspection and "/inspection" in path:
                value += 120

            if intent == ChatProductQueryIntent.STRUCTURE:
                if "/structure" in path:
                    value += 150

                if "structure" in haystack or "estrutura" in haystack or "bom" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

                if "search" in path:
                    value -= 80

            elif intent == ChatProductQueryIntent.STOCK:
                if "/products/{code}/stock" in haystack or path.endswith("/stock"):
                    value += 120

                if "stock" in haystack or "estoque" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

            elif intent == ChatProductQueryIntent.SALES:
                if self._is_product_sales_summary_path(path):
                    value += 280

                if "/sales" in path and "billing" not in path and "open-orders" not in path:
                    value += 60

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 120

                if "analyser" in haystack:
                    value -= 40

            elif intent == ChatProductQueryIntent.PARENTS:
                if "/parents" in path:
                    value += 200

                if "parent" in haystack or "pai" in haystack:
                    value += 40

                if "analyser" in haystack:
                    value -= 40

                if "search" in path:
                    value -= 80

            elif intent == ChatProductQueryIntent.SUMMARY:
                if "/products/{code}/summary" in path or path.endswith("/summary"):
                    value += 260

                if "summary" in haystack and "product" in haystack:
                    value += 40

                if "/products/{code}/analyser" in haystack or path.endswith("/analyser"):
                    value -= 120

                if "analyser" in haystack or "analyzer" in haystack:
                    value -= 80

                if path == "/products/{code}":
                    value += 30

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 90

                if "search" in path:
                    value -= 100

            elif intent == ChatProductQueryIntent.ANALYSER:
                if "/products/{code}/analyser" in haystack or path.endswith("/analyser"):
                    value += 280

                if "analyser" in haystack or "analyzer" in haystack:
                    value += 60

                if "/summary" in path:
                    value -= 100

                if path == "/products/{code}":
                    value += 40

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 90

                if "search" in path:
                    value -= 100

            elif intent == ChatProductQueryIntent.DESCRIPTION:
                if path == "/products/{code}":
                    value += 200

                if wants_product_summary and "/summary" in path:
                    value += 80

                if wants_full_analyser and "/products/{code}/analyser" in haystack:
                    value += 180
                elif not wants_product_summary and "/products/{code}/analyser" in haystack:
                    value += 120

                if "/description" in path:
                    value += 150

                if wants_product_summary and "analyser" in haystack:
                    value -= 80

                if "stock" in path or "structure" in path or "parents" in path:
                    value -= 80

                if "search" in path:
                    value -= 100

            else:
                if not has_specific_sub_intent:
                    if "/products/{code}/analyser" in haystack:
                        value += 100

                    if "analyser" in haystack or "analyzer" in haystack:
                        value += 60

                if "/products/{code}" in haystack:
                    value += 25

            if "product" in haystack or "products" in haystack or "produto" in haystack:
                value += 20

            if "search" in haystack or "buscar" in haystack or "busca" in haystack:
                value += 8

            if intent != ChatProductQueryIntent.STOCK and (
                "stock" in haystack or "estoque" in haystack
            ):
                value += 6

            if "structure" in haystack or "estrutura" in haystack:
                value += 5

            value += self._provider_preference_bonus(action)

            return value

        return sorted(candidates, key=score, reverse=True)

    @staticmethod
    def _is_product_sales_summary_path(path: str) -> bool:
        lowered = str(path or "").lower().rstrip("/")

        if "open-orders" in lowered or "/billing" in lowered:
            return False

        return lowered.endswith("/sales") and "/products/" in lowered

    @classmethod
    def _provider_preference_bonus(cls, action: dict) -> int:
        from app.infrastructure.config.settings import Settings

        if not Settings.CHAT_PREFER_API_EXTERNA_PROVIDER:
            return 0

        action_id = str(action.get("actionId") or "").lower()

        if action_id.startswith("api_externa."):
            return 95

        if action_id.startswith("api_delpi."):
            return -120

        return 0

    @classmethod
    def _clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        try:
            depth = int(value)
        except (TypeError, ValueError):
            depth = 10

        lowered = str(path or "").lower()
        cap = (
            cls.HIERARCHICAL_PRODUCT_MAX_DEPTH
            if "/structure" in lowered or "/parents" in lowered
            else 99
        )

        return min(max(depth, 1), cap)

    @classmethod
    def _is_drawing_analyser_request(cls, message: str | None, path: str) -> bool:
        if "/analyser" not in str(path or "").lower():
            return False

        from app.domain.services.chat_drawing_intent_service import (
            ChatDrawingIntentService,
        )

        return ChatDrawingIntentService.is_drawing_analysis_request(message or "")

    def _build_product_parameters(self, action: dict, code: str, *, message: str | None = None) -> dict:
        parameters = {}
        path = (action.get("path") or "").lower()
        is_full_listing = "/structure" in path or "/parents" in path
        normalized = (
            ChatMessageNormalizationService.normalize_for_matching(message)
            if message
            else ""
        )

        branch_code = (
            ChatOperationalRefinementService.extract_branch_code(normalized)
            if normalized
            else None
        )
        warehouse_code = (
            ChatOperationalRefinementService.extract_warehouse_code(normalized)
            if normalized
            else None
        )
        requested_page_size = (
            ChatOperationalRefinementService.extract_requested_page_size(normalized)
            if normalized
            else None
        )
        requested_page = (
            ChatOperationalRefinementService.extract_requested_page(normalized)
            if normalized
            else None
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {
                "code",
                "product_code",
                "productcode",
                "codigo",
                "cod_produto",
                "produto",
                "item",
                "id",
            }:
                parameters[name] = code

            elif lowered in {
                "query",
                "q",
                "search",
                "description",
                "descricao",
                "term",
            }:
                parameters[name] = code

            elif lowered == "page":
                parameters[name] = requested_page or 1

            elif lowered in {"page_size", "pagesize", "limit"}:
                if requested_page_size is not None:
                    parameters[name] = requested_page_size
                elif self._is_drawing_analyser_request(message, path):
                    parameters[name] = 50
                else:
                    parameters[name] = 200 if is_full_listing else 50

            elif lowered in {"max_depth", "maxdepth", "depth", "nivel", "levels"}:
                if self._is_drawing_analyser_request(message, path):
                    parameters[name] = 10
                else:
                    parameters[name] = (
                        self.HIERARCHICAL_PRODUCT_MAX_DEPTH
                        if is_full_listing
                        else min(10, self.HIERARCHICAL_PRODUCT_MAX_DEPTH)
                    )

            elif lowered in {"branch", "filial", "branch_code", "branchcode"} and branch_code:
                parameters[name] = branch_code

            elif lowered in {
                "warehouse",
                "armazem",
                "armazém",
                "warehouse_code",
                "deposito",
                "depósito",
                "location",
                "local",
            } and warehouse_code:
                parameters[name] = warehouse_code

            elif lowered == "view" and "/analyser" in path:
                from app.domain.services.chat_product_query_intent_service import (
                    ChatProductQueryIntentService,
                )

                normalized_message = (
                    ChatMessageNormalizationService.normalize_for_matching(message)
                    if message
                    else ""
                )
                if ChatProductQueryIntentService._looks_like_full_analyser_question(
                    normalized_message
                ):
                    parameters[name] = "full"
                else:
                    parameters[name] = "summary"

        return parameters
