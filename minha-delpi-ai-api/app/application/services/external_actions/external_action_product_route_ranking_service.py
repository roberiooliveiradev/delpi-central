"""Ranking heurístico de rotas de produto — fallback ambíguo pós-registry (DOCIE Fase 6)."""

from __future__ import annotations

from app.domain.services.chat_product_overview_intent_service import (
    ChatProductOverviewIntentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class ExternalActionProductRouteRankingService:
    """Desempate residual quando registry e routeSegment não resolvem a rota."""

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
        wants_sales = ChatProductQueryIntentService._looks_like_sales_question(
            normalized
        ) and not wants_sale_pricing

        wants_product_overview = ChatProductOverviewIntentService.is_product_overview_message(
            message
        )
        wants_product_summary = (
            wants_product_overview
            or ChatProductQueryIntentService._looks_like_product_summary_route_question(
                normalized
            )
        )
        wants_full_analyser = ChatProductQueryIntentService._looks_like_full_analyser_question(
            normalized
        )
        wants_structure = ChatProductQueryIntentService._looks_like_structure_question(
            normalized
        )
        wants_stock = (
            ChatProductQueryIntentService._looks_like_stock_question(normalized)
            and not wants_full_analyser
        )
        wants_parents = ChatProductQueryIntentService._looks_like_parents_question(
            normalized
        )
        wants_invoices = ChatProductQueryIntentService._looks_like_invoices_route_question(
            normalized
        )
        wants_inbound = (
            ChatProductQueryIntentService._looks_like_inbound_invoice_route_question(
                normalized
            )
        )
        wants_outbound = (
            ChatProductQueryIntentService._looks_like_outbound_invoice_route_question(
                normalized
            )
        )

        def score(action: dict) -> int:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ["actionId", "operationId", "path", "summary", "description"]
            ).lower()
            path = str(action.get("path") or "").lower()

            value = 0

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

            if wants_sales and ExternalActionProductRouteRankingService.is_product_sales_summary_path(path):
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

            if wants_parents and "/parents" in path:
                value += 120

            if wants_invoices:
                if wants_outbound and "/outbound-invoice" in path:
                    value += 130
                elif wants_inbound and "/inbound-invoice" in path:
                    value += 130
                elif "/inbound-invoice" in path or "/outbound-invoice" in path:
                    value += 120

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
