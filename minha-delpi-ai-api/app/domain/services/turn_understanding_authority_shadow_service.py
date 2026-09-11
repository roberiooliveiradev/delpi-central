"""E2.S4 — shadow compare authority heuristics vs contrato TU (+ dials por família)."""

from __future__ import annotations

import logging
from typing import Any

from app.domain.entities.turn_understanding import TurnUnderstanding

logger = logging.getLogger(__name__)


class TurnUnderstandingAuthorityShadowService:
    @classmethod
    def compare(
        cls,
        message: str,
        contract: TurnUnderstanding | None,
    ) -> dict[str, Any] | None:
        if contract is None:
            return None

        from app.domain.services.chat_conversational_intelligence_flag_service import (
            ChatConversationalIntelligenceFlagService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )
        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )
        from app.domain.services.turn_understanding_product_intent_mapper_service import (
            TurnUnderstandingProductIntentMapperService,
        )
        from app.domain.services.turn_understanding_production_intent_mapper_service import (
            TurnUnderstandingProductionIntentMapperService,
        )
        from app.domain.services.turn_understanding_kpi_intent_mapper_service import (
            TurnUnderstandingKpiIntentMapperService,
        )
        from app.domain.services.turn_understanding_generic_intent_mapper_service import (
            TurnUnderstandingGenericIntentMapperService,
        )
        from app.domain.services.chat_intent_router.chat_intent_router_classify_service import (
            ChatIntentRouterClassifyService,
        )

        product = str(
            ChatProductQueryIntentService.detect(message, force_legacy=True) or ""
        ).strip()
        candidate_product = TurnUnderstandingProductIntentMapperService.from_understanding(
            contract
        )
        production = ChatProductionOperationalIntentService.resolve(
            message,
            force_legacy=True,
        )
        production_name = production.name if production is not None else None
        candidate_production = TurnUnderstandingProductionIntentMapperService.from_understanding(
            contract
        )
        candidate_production_name = (
            candidate_production.name if candidate_production is not None else None
        )
        kpi = ChatDepartmentKpiIntentService.resolve(message, force_legacy=True)
        kpi_hit = kpi is not None
        candidate_kpi = TurnUnderstandingKpiIntentMapperService.from_understanding(contract)
        candidate_kpi_token = (
            str(candidate_kpi.path_token) if candidate_kpi is not None else None
        )

        goal_text = " ".join(goal.intent for goal in contract.goals).lower()
        entity_codes = {
            str(goal.entities.get("productCode") or "").strip()
            for goal in contract.goals
            if goal.entities.get("productCode")
        }
        extracted_code = ChatProductQueryIntentService.extract_product_code(message) or ""

        agree_product = True
        if product and product not in {"full", "multi_scope"}:
            tokens = {
                "stock": ("estoque", "saldo"),
                "structure": ("estrutura",),
                "sales": ("venda", "fatur"),
                "suppliers": ("fornecedor",),
            }
            needles = tokens.get(product, (product,))
            agree_product = any(token in goal_text for token in needles) or (
                bool(extracted_code) and extracted_code in entity_codes
            )
            if candidate_product:
                agree_product = agree_product or candidate_product == product
        elif extracted_code:
            agree_product = extracted_code in entity_codes or not entity_codes

        agree_production = True
        if production_name:
            agree_production = any(
                token in goal_text
                for token in ("produc", "agenda", "program", "perda", "consumo", "schedule")
            )
            if candidate_production_name:
                agree_production = agree_production or (
                    candidate_production_name == production_name
                )

        agree_kpi = True
        if kpi_hit:
            agree_kpi = any(
                token in goal_text for token in ("kpi", "indicador", "receita", "meta", "filial")
            )
            if candidate_kpi_token and kpi is not None:
                agree_kpi = agree_kpi or candidate_kpi_token == kpi.path_token

        agree_compound = contract.subtask_count >= 2 or product != "multi_scope"
        generic = TurnUnderstandingGenericIntentMapperService.from_understanding(contract)
        legacy_route = ChatIntentRouterClassifyService.classify(message)
        legacy_intent = str(legacy_route.intent or "")
        legacy_sub = str(legacy_route.sub_intent or "")
        agree_no_tool = True
        if generic.no_tool is False:
            agree_no_tool = legacy_intent in {"small_talk", "utility", "identity"}
        elif generic.no_tool is True:
            agree_no_tool = legacy_intent not in {"small_talk", "utility", "identity"}
        agree_presentation = True
        if generic.presentation_view:
            agree_presentation = legacy_intent in {
                "presentation_task",
                "follow_up",
            } or legacy_sub == "format_refinement"
        agree_compare = True
        if generic.is_reasoning:
            agree_compare = (
                legacy_intent in {"analysis", "text_task"}
                or legacy_sub in {"analysis", "data_interpretation", "compound"}
            )

        cutover_product = (
            ChatConversationalIntelligenceFlagService.product_family_cutover_enabled()
        )
        cutover_production = (
            ChatConversationalIntelligenceFlagService.production_family_cutover_enabled()
        )
        cutover_kpi = ChatConversationalIntelligenceFlagService.kpi_family_cutover_enabled()
        cutover_no_tool = (
            ChatConversationalIntelligenceFlagService.no_tool_family_cutover_enabled()
        )
        cutover_presentation = (
            ChatConversationalIntelligenceFlagService.presentation_family_cutover_enabled()
        )
        cutover_compare = (
            ChatConversationalIntelligenceFlagService.compare_explain_family_cutover_enabled()
        )

        shadow = {
            "kind": "turn_understanding_authority",
            "cutover": bool(cutover_product),
            "cutoverProduction": bool(cutover_production),
            "cutoverKpi": bool(cutover_kpi),
            "cutoverNoTool": bool(cutover_no_tool),
            "cutoverPresentation": bool(cutover_presentation),
            "cutoverCompareExplain": bool(cutover_compare),
            "goalCount": contract.subtask_count,
            "productIntent": product or None,
            "candidateProductIntent": candidate_product,
            "productionKind": production_name,
            "candidateProductionKind": candidate_production_name,
            "kpiMatched": kpi_hit,
            "candidateKpi": candidate_kpi_token,
            "candidateNoTool": generic.no_tool,
            "candidatePresentationView": generic.presentation_view,
            "candidateIsReasoning": generic.is_reasoning,
            "agreeProduct": bool(agree_product),
            "agreeProduction": bool(agree_production),
            "agreeKpi": bool(agree_kpi),
            "agreeNoTool": bool(agree_no_tool),
            "agreePresentation": bool(agree_presentation),
            "agreeCompareExplain": bool(agree_compare),
            "agreeCompound": bool(agree_compound),
            "agree": bool(agree_product and agree_production and agree_kpi),
        }
        cls.record(shadow)
        return shadow

    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "turn_understanding_authority_shadow",
            extra={
                "metric": "turn_understanding_authority_shadow",
                "agree": bool(shadow.get("agree")),
                "agreeProduct": bool(shadow.get("agreeProduct")),
                "agreeProduction": bool(shadow.get("agreeProduction")),
                "agreeKpi": bool(shadow.get("agreeKpi")),
                "goalCount": int(shadow.get("goalCount") or 0),
                "productIntent": shadow.get("productIntent"),
                "candidateProductIntent": shadow.get("candidateProductIntent"),
                "productionKind": shadow.get("productionKind"),
                "candidateProductionKind": shadow.get("candidateProductionKind"),
                "candidateKpi": shadow.get("candidateKpi"),
                "cutover": bool(shadow.get("cutover")),
                "cutoverProduction": bool(shadow.get("cutoverProduction")),
                "cutoverKpi": bool(shadow.get("cutoverKpi")),
                "cutoverNoTool": bool(shadow.get("cutoverNoTool")),
                "cutoverPresentation": bool(shadow.get("cutoverPresentation")),
                "cutoverCompareExplain": bool(shadow.get("cutoverCompareExplain")),
                "agreeNoTool": bool(shadow.get("agreeNoTool")),
                "agreePresentation": bool(shadow.get("agreePresentation")),
                "agreeCompareExplain": bool(shadow.get("agreeCompareExplain")),
            },
        )
