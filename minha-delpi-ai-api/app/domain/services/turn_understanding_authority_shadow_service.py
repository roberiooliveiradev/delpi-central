"""E2.S4 — shadow compare authority heuristics vs contrato TU (sem cutover)."""

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

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )
        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )

        product = str(ChatProductQueryIntentService.detect(message) or "").strip()
        production = ChatProductionOperationalIntentService.resolve(message)
        production_name = production.name if production is not None else None
        kpi = ChatDepartmentKpiIntentService.resolve(message)
        kpi_hit = kpi is not None

        goal_text = " ".join(goal.intent for goal in contract.goals).lower()
        entity_codes = {
            str(goal.entities.get("productCode") or "").strip()
            for goal in contract.goals
            if goal.entities.get("productCode")
        }
        extracted_code = ChatProductQueryIntentService.extract_product_code(message) or ""

        agree_product = True
        if product and product not in {"full", "multi_scope"}:
            # Authority named a product intent — TU should mention related prose or code.
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
        elif extracted_code:
            agree_product = extracted_code in entity_codes or not entity_codes

        agree_production = True
        if production_name:
            agree_production = any(
                token in goal_text
                for token in ("produc", "agenda", "program", "perda", "consumo", "schedule")
            )

        agree_kpi = True
        if kpi_hit:
            agree_kpi = any(
                token in goal_text for token in ("kpi", "indicador", "receita", "meta", "filial")
            )

        agree_compound = contract.subtask_count >= 2 or product != "multi_scope"

        shadow = {
            "kind": "turn_understanding_authority",
            "cutover": False,
            "goalCount": contract.subtask_count,
            "productIntent": product or None,
            "productionKind": production_name,
            "kpiMatched": kpi_hit,
            "agreeProduct": bool(agree_product),
            "agreeProduction": bool(agree_production),
            "agreeKpi": bool(agree_kpi),
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
                "productionKind": shadow.get("productionKind"),
            },
        )
