"""Inferência canônica de `profile_name` para tabelas operacionais — Playbook 12 R23."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)

_ENTITY_TABLE_PROFILES: dict[str, str] = {
    "product_stock": "stockProductPositions",
    "product_guide": "guide",
    "product_inspection": "analyserInspection",
    "product_search": "productSearchBasic",
    "product_purchases": "purchaseOrderList",
    "product_purchase_price_history": "purchaseBudgetHistoryDetail",
    "product_purchase_budget_history": "purchaseBudgetHistoryDetail",
    "product_production_status": "factoryProductionDetail",
    "product_shipping_status": "shippingStatusDetail",
    "product_structure_exclusivity": "structureExclusivityDetail",
    "product_raw_material_price_intelligence": "mpPriceHistoryDetail",
    "product_cost_impact_simulation": "costImpactMaterials",
    "product_pricing": "salePricingDetail",
    "product_last_purchase": "lastPurchaseDetail",
    "product_factory_status": "factoryProductionDetail",
}


class ChatPresentationTableProfileInferenceService:
    """Resolve hints de `tableProfiles` a partir de entidade, rota e amostra de row."""

    @classmethod
    def infer_profile_name(
        cls,
        *,
        path: str = "",
        entity: str | None = None,
        sample_row: dict[str, Any] | None = None,
        column_labels: ExternalActionColumnLabelService | None = None,
    ) -> str | None:
        token = str(entity or "").strip()

        if token:
            hinted = _ENTITY_TABLE_PROFILES.get(token)

            if hinted:
                return hinted

        labels = column_labels or ExternalActionColumnLabelService()

        if isinstance(sample_row, dict) and sample_row:
            detected = labels.detect_table_profile(sample_row, path=path)

            if detected:
                return detected

        return None
