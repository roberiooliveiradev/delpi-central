"""Ranking heurístico de rotas de produto — fallback FULL (DOCIE Fase 4)."""

from __future__ import annotations

import re

from app.domain.services.chat_product_overview_intent_service import (
    ChatProductOverviewIntentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductRouteRankingService:

    def rank_product_actions(
        self,
        candidates: list[dict],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        message: str | None = None,
        route_segment: str | None = None,
        allowed_action_ids: list[str] | None = None,
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

            elif wants_sales and ExternalActionProductRouteRankingService.is_product_sales_summary_path(path):
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

            return value

        order = {
            str(action_id): index
            for index, action_id in enumerate(allowed_action_ids or [])
            if str(action_id).strip()
        }

        def sort_key(action: dict) -> tuple[int, int]:
            action_id = str(action.get("actionId") or "")
            return (score(action), -order.get(action_id, 999))

        return sorted(candidates, key=sort_key, reverse=True)


    @staticmethod
    def is_product_sales_summary_path(path: str) -> bool:
        lowered = str(path or "").lower().rstrip("/")

        if "open-orders" in lowered or "/billing" in lowered:
            return False

        return lowered.endswith("/sales") and "/products/" in lowered

