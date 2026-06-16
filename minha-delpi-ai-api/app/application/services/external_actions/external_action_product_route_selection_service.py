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
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductRouteSelectionService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15

    def __init__(self, repository) -> None:
        self.repository = repository

    def _find_allowed_actions_by_markers(
        self,
        *,
        path_markers: list[str],
        operation_markers: list[str],
        allowed_action_ids: list[str],
        method: str = "GET",
    ) -> list[dict]:
        """Resolve actions autorizadas pelo catálogo — não depende de ranking semântico."""
        allowed = {str(item) for item in allowed_action_ids if str(item).strip()}

        if not allowed or (not path_markers and not operation_markers):
            return []

        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        matches: list[dict] = []

        for action in list_actions():
            if str(action.get("actionId") or "") not in allowed:
                continue

            if str(action.get("method") or "").upper() != method.upper():
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if path_markers and not any(marker in path for marker in path_markers):
                continue

            if operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                if path_markers:
                    continue

            if not path_markers and operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                continue

            matches.append(action)

        return matches

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
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = self._load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

        if not candidates:
            return None

        if intent == ChatProductQueryIntent.FULL and not route_segment:
            normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")

            if not ChatProductQueryIntentService.has_actionable_product_route_intent(
                message,
                normalized=normalized,
            ):
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
                previous_messages=previous_messages,
            )

            if not parameters:
                continue

            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            if (
                ChatOperationalDateParameterService.action_requires_explicit_date(action)
                and not ChatOperationalDateParameterService.parameters_have_date(
                    action,
                    parameters,
                )
            ):
                continue

            if parameters:
                path = str(action.get("path") or "").lower()
                if "/directives/" in path:
                    reason = ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "productDirectives",
                    )
                else:
                    reason = ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "productOperational",
                    )

                if branch_code := (
                    ChatOperationalRefinementService.extract_branch_code(
                        ChatMessageNormalizationService.normalize_for_matching(message)
                    )
                ):
                    reason = ExternalActionResponseContentService.format(
                        "selectionReasons",
                        "productStockBranchRefinement",
                        product_code=product_code,
                        branch_code=branch_code,
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
        wants_raw_material_price_intelligence = (
            ChatProductQueryIntentService._looks_like_raw_material_price_intelligence_question(
                normalized
            )
        )
        wants_cost_impact_simulation = (
            ChatProductQueryIntentService._looks_like_cost_impact_simulation_question(
                normalized
            )
        )
        wants_last_purchase = (
            ChatProductQueryIntentService._looks_like_last_purchase_question(normalized)
        )
        wants_purchase_price_history = (
            ChatProductQueryIntentService._looks_like_purchase_price_history_question(
                normalized
            )
        )
        wants_purchase_budget_history = (
            ChatProductQueryIntentService._looks_like_purchase_budget_history_question(
                normalized
            )
        )
        wants_directives = ChatProductQueryIntentService._looks_like_directives_question(
            normalized
        )
        wants_sale_pricing = ChatProductQueryIntentService._looks_like_sale_pricing_question(
            normalized
        )
        wants_price_analysis = (
            ChatProductQueryIntentService._looks_like_price_analysis_question(normalized)
        )
        wants_purchases = any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "purchasesTerms",
            )
        ) and not (
            wants_last_purchase
            or wants_purchase_price_history
            or wants_purchase_budget_history
            or wants_raw_material_price_intelligence
        )
        wants_billing = ChatProductQueryIntentService._looks_like_billing_question(
            normalized
        )
        wants_factory_status = (
            ChatProductQueryIntentService._looks_like_factory_status_question(
                normalized
            )
        )
        wants_production_status = (
            ChatProductQueryIntentService._looks_like_production_status_question(
                normalized
            )
        )
        wants_shipping_status = (
            ChatProductQueryIntentService._looks_like_shipping_status_question(
                normalized
            )
        )
        wants_structure_exclusivity = (
            ChatProductQueryIntentService._looks_like_structure_exclusivity_question(
                normalized
            )
        )
        wants_open_orders = any(
            term in normalized
            for term in ("carteira", "pedidos em aberto", "pedido em aberto", "open-orders")
        )
        wants_sales = ChatProductQueryIntentService._looks_like_sales_question(
            normalized
        ) and not wants_open_orders and not wants_sale_pricing
        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        wants_product_overview = ChatProductOverviewIntentService.is_product_overview_message(
            message
        )
        wants_product_summary = wants_product_overview or any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "summaryTerms",
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
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "guideTerms",
            )
        )
        wants_suppliers = any(
            term in normalized
            for term in ("fornecedor", "fornecedore", "fornece", "supplier")
        ) or bool(re.search(r"\bfornece\b", normalized))
        wants_pricing = any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "pricingTerms",
            )
        ) and not (
            wants_raw_material_price_intelligence
            or wants_cost_impact_simulation
            or wants_last_purchase
            or wants_purchase_price_history
            or wants_purchase_budget_history
        )
        wants_customers = any(
            term in normalized
            for term in ("cliente", "customer")
        )
        wants_parents = any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "parentsTerms",
            )
        )
        wants_movements = any(
            term in normalized
            for term in ("movimentaç", "movimentac", "internal-movement")
        )
        wants_invoices = any(
            term in normalized
            for term in ExternalActionResponseContentService.list(
                "actionSelection",
                "productRouteRanking",
                "invoicesTerms",
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
        elif inherited_segment == "raw-material-price-intelligence":
            wants_raw_material_price_intelligence = True
        elif inherited_segment == "cost-impact-simulation":
            wants_cost_impact_simulation = True
        elif inherited_segment == "last-purchase":
            wants_last_purchase = True
        elif inherited_segment == "purchase-price-history":
            wants_purchase_price_history = True
        elif inherited_segment == "purchase-budget-history":
            wants_purchase_budget_history = True
        elif inherited_segment == "directives":
            wants_directives = True

        has_specific_sub_intent = (
            wants_purchases or wants_sales or wants_open_orders or wants_structure
            or wants_guide or wants_suppliers or wants_pricing or wants_customers
            or wants_parents or wants_movements or wants_invoices or wants_inspection
            or wants_billing
            or wants_factory_status
            or wants_production_status
            or wants_shipping_status
            or wants_structure_exclusivity
            or wants_raw_material_price_intelligence
            or wants_cost_impact_simulation
            or wants_last_purchase
            or wants_purchase_price_history
            or wants_purchase_budget_history
            or wants_directives
            or wants_product_summary
            or wants_product_overview
            or wants_full_analyser
            or wants_price_analysis
        )
        suppress_api_externa_provider_bias = (
            wants_factory_status
            or wants_production_status
            or wants_shipping_status
            or wants_structure_exclusivity
            or wants_raw_material_price_intelligence
            or wants_cost_impact_simulation
            or wants_last_purchase
            or wants_purchase_price_history
            or wants_purchase_budget_history
            or wants_directives
            or wants_sale_pricing
            or wants_price_analysis
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

            if wants_sale_pricing and "/pricing" in path:
                value += 130

            if wants_price_analysis and "analyser" in path:
                value += 135

            if wants_price_analysis and "raw-material-price-intelligence" in path:
                value += 140

            if wants_price_analysis and "/pricing" in path:
                value += 125

            if wants_price_analysis and "production-status" in path:
                value -= 110

            if wants_price_analysis and "/structure" in path and not wants_structure:
                value -= 90

            if wants_sale_pricing and "/sales" in path and "/pricing" not in path:
                value -= 110

            if wants_sale_pricing and (
                "raw-material-price-intelligence" in path
                or "last-purchase" in path
                or "purchase-price-history" in path
                or "purchase-budget-history" in path
            ):
                value -= 100

            if (
                wants_raw_material_price_intelligence
                or wants_last_purchase
                or wants_purchase_price_history
                or wants_purchase_budget_history
            ) and "/pricing" in path and not wants_sale_pricing:
                value -= 90

            if wants_directives and "/structure" in path and "/directives/" not in path:
                value -= 120

            if wants_directives and "last-purchase" in path and "/directives/" not in path:
                value -= 120

            if wants_directives and "/suppliers" in path and "/directives/" not in path:
                value -= 120

            if wants_last_purchase and "/purchases" in path and "last-purchase" not in path:
                value -= 80

            if wants_purchase_budget_history and "/purchases" in path:
                value -= 85

            if wants_purchase_price_history and "/purchases" in path:
                value -= 70

            if wants_cost_impact_simulation and path.rstrip("/").endswith("/structure"):
                value -= 85

            if wants_cost_impact_simulation and "cost-impact-simulation" not in path and "/structure" in path:
                value -= 60

            if wants_structure and not wants_cost_impact_simulation and "cost-impact-simulation" in path:
                value -= 90

            if wants_production_status and wants_factory_status:
                if any(
                    marker in normalized
                    for marker in (
                        "fabril",
                        "fabrica",
                        "fábrica",
                        "completo na fabrica",
                        "completo na fábrica",
                    )
                ):
                    if "production-status" in path:
                        value -= 80
                elif any(
                    marker in normalized
                    for marker in (
                        "apontamento",
                        " sh6010",
                        "playbook produtivo",
                        "analise produtiva",
                        "análise produtiva",
                    )
                ):
                    if "factory-status" in path:
                        value -= 80

            if wants_shipping_status and "/inspection" in path and "shipping-status" not in path:
                value -= 90

            if wants_shipping_status and "factory-status" in path and not wants_factory_status:
                value -= 70

            if wants_structure_exclusivity and path.rstrip("/").endswith("/structure"):
                value -= 80

            if wants_structure_exclusivity and "analyser" in haystack and not wants_full_analyser:
                value -= 60

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

            if wants_structure_exclusivity and "/structure/exclusivity" not in path and "/structure" in path:
                value -= 40

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

            if wants_inspection and "/inspection" in path and not wants_shipping_status:
                value += 120

            if wants_inspection and wants_shipping_status and "/inspection" in path:
                value -= 90

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

            value += self._provider_preference_bonus(
                action,
                suppress_playbook_bias=suppress_api_externa_provider_bias,
            )

            return value

        return sorted(candidates, key=score, reverse=True)

    @staticmethod
    def _is_product_sales_summary_path(path: str) -> bool:
        lowered = str(path or "").lower().rstrip("/")

        if "open-orders" in lowered or "/billing" in lowered:
            return False

        return lowered.endswith("/sales") and "/products/" in lowered

    @classmethod
    def _provider_preference_bonus(
        cls,
        action: dict,
        *,
        suppress_playbook_bias: bool = False,
    ) -> int:
        if suppress_playbook_bias:
            return 0

        try:
            from app.application.services.chat_intelligence_runtime_access import (
                resolve_chat_intelligence_runtime,
            )

            prefer_api_externa = (
                resolve_chat_intelligence_runtime().prefer_api_externa_provider
            )
        except RuntimeError:
            from app.infrastructure.config.settings import Settings

            prefer_api_externa = bool(
                getattr(Settings, "CHAT_PREFER_API_EXTERNA_PROVIDER", False)
            )

        if suppress_playbook_bias or not prefer_api_externa:
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

    def _build_product_parameters(
        self,
        action: dict,
        code: str,
        *,
        message: str | None = None,
        previous_messages: list | None = None,
    ) -> dict:
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
                "identifier",
                "referencia",
                "referência",
                "customer_reference",
                "delpi_code",
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

            elif lowered == "adjustment_percent":
                percent = self._extract_adjustment_percent(normalized)

                if percent is not None:
                    parameters[name] = percent

            elif lowered == "top_n":
                top_n = self._extract_top_n(normalized)

                if top_n is not None:
                    parameters[name] = top_n

            elif lowered == "price_source":
                if any(
                    term in normalized
                    for term in (
                        "ultima compra",
                        "última compra",
                        "last_purchase",
                        "last purchase",
                    )
                ):
                    parameters[name] = "last_purchase"
                elif any(
                    term in normalized
                    for term in (
                        "custo padrao",
                        "custo padrão",
                        "standard_cost",
                        "standard cost",
                    )
                ):
                    parameters[name] = "standard_cost"

        from app.domain.services.chat_operational_date_parameter_service import (
            ChatOperationalDateParameterService,
        )

        return ChatOperationalDateParameterService.merge_into_parameters(
            action,
            message,
            parameters,
            previous_messages=previous_messages,
        )

    @staticmethod
    def _extract_adjustment_percent(normalized: str) -> float | None:
        if not normalized:
            return None

        patterns = (
            r"(?:aumento|reajuste|subir|simul\w*)\s*(?:de\s*)?([+-]?\d+(?:[.,]\d+)?)\s*(?:%|percento|por\s*cento)",
            r"([+-]?\d+(?:[.,]\d+)?)\s*(?:%|percento|por\s*cento)\s*(?:de\s*)?(?:aumento|reajuste|simul)",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized)

            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    return None

        return None

    def select_exclusive_raw_material_catalog(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if not ChatProductQueryIntentService._looks_like_exclusive_raw_material_catalog_question(
            normalized
        ):
            return None

        candidates = self._load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            if "exclusive-raw-materials/catalog" not in path:
                continue

            parameters = self._build_exclusive_catalog_parameters(
                action,
                message=message,
                normalized=normalized,
            )

            if not parameters:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "exclusiveRawMaterialCatalog",
                ),
            }

        return None

    def select_product_directives(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if not ChatProductQueryIntentService._looks_like_directives_question(normalized):
            return None

        identifier = ChatProductQueryIntentService.extract_product_code(message or "")

        if not identifier:
            return None

        candidates = self._find_allowed_actions_by_markers(
            path_markers=["/directives/"],
            operation_markers=["get_product_directives"],
            allowed_action_ids=allowed_action_ids,
        )

        if not candidates:
            candidates = self._load_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            if "/directives/" not in path:
                continue

            parameters = self._build_product_parameters(
                action,
                identifier,
                message=message,
            )

            if not parameters:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "productDirectives",
                ),
            }

        return None

    def _build_exclusive_catalog_parameters(
        self,
        action: dict,
        *,
        message: str,
        normalized: str,
    ) -> dict:
        parameters: dict = {}
        requested_page_size = ChatOperationalRefinementService.extract_requested_page_size(
            normalized
        )
        requested_page = ChatOperationalRefinementService.extract_requested_page(normalized)
        product_code = ChatProductQueryIntentService.extract_product_code(message or "")

        finished_product_markers = (
            "produto",
            "produtos",
            " pa ",
            " pas ",
            "acabado",
            "acabados",
        )
        default_view = (
            "by_finished_product"
            if any(marker in normalized for marker in finished_product_markers)
            else "by_material"
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")
            if not name:
                continue

            lowered = name.lower()

            if lowered == "view":
                parameters[name] = default_view
            elif lowered == "limit":
                parameters[name] = requested_page_size or 10
            elif lowered == "offset":
                page = requested_page or 1
                page_size = requested_page_size or 10
                parameters[name] = (page - 1) * page_size
            elif lowered in {"finished_product_code", "finishedproductcode"} and product_code:
                parameters[name] = product_code
            elif lowered in {"raw_material_code", "rawmaterialcode"} and product_code:
                parameters[name] = product_code
            elif lowered in {"max_depth", "maxdepth"}:
                parameters[name] = self.HIERARCHICAL_PRODUCT_MAX_DEPTH

        if "view" not in {key.lower() for key in parameters}:
            parameters["view"] = default_view

        if "limit" not in {key.lower() for key in parameters}:
            parameters["limit"] = requested_page_size or 50

        return parameters

    @staticmethod
    def _extract_top_n(normalized: str) -> int | None:
        if not normalized:
            return None

        patterns = (
            r"\btop\s*(\d+)\b",
            r"\b(\d+)\s*(?:principais|maiores|primeir)",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized)

            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    return None

        return None
