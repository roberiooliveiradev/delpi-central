"""Roteamento de apresentação por meta.entity (Fase 7 — contrato api-delpi)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


CHAT_CRITICAL_ENTITIES: frozenset[str] = frozenset(
    {
        "product_search",
        "product",
        "product_stock",
        "product_structure",
        "product_structure_exclusivity",
        "exclusive_raw_materials_catalog",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_raw_material_price_intelligence",
        "product_cost_impact_simulation",
        "product_last_purchase",
        "product_purchase_price_history",
        "product_purchase_budget_history",
        "product_parents",
        "product_guide",
        "product_inspection",
        "product_pricing",
        "product_purchases",
        "product_sales",
        "product_open_orders",
        "product_billing",
        "product_suppliers",
        "product_customers",
        "product_internal_movements",
        "product_inbound_invoice_items",
        "product_outbound_invoice_items",
    }
)

PROFILE_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "product_search",
        "product",
        "product_stock",
        "product_structure",
        "product_structure_exclusivity",
        "exclusive_raw_materials_catalog",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_raw_material_price_intelligence",
        "product_cost_impact_simulation",
        "product_last_purchase",
        "product_purchase_price_history",
        "product_purchase_budget_history",
        "product_parents",
        "product_guide",
        "product_inspection",
        "product_pricing",
        "product_purchases",
        "product_suppliers",
        "product_customers",
        "product_internal_movements",
        "product_inbound_invoice_items",
        "product_outbound_invoice_items",
        "product_sales",
        "product_open_orders",
        "product_billing",
    }
)

PRODUCT_LIST_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "product_purchases",
        "product_suppliers",
        "product_customers",
        "product_internal_movements",
        "product_inbound_invoice_items",
        "product_outbound_invoice_items",
        "product_open_orders",
    }
)

KPI_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "supplies_cpv",
        "supplies_otd",
        "supplies_stock_value",
        "supplies_inventory_turnover",
        "supplies_negotiation_savings",
        "financial_rol",
        "financial_ebitda_pct",
        "financial_fixed_cost_pct",
        "financial_pmr",
        "commercial_rol_target",
        "commercial_rol_series",
        "sales_conversion_rate",
        "new_clients_average",
        "sales_order_otd",
        "new_business_rol_pct",
        "new_clients_rol_pct",
        "direct_labor_cost_pct",
        "production_cost_pct",
        "depreciation_pct",
        "production_oee_series",
        "production_otd_series",
        "overall_equipment_effectiveness",
        "production_otd",
        "eficiencia_fabril_dashboard",
        "hr_snapshot",
        "hr_active_pdi_count",
        "hr_performance_reviews_completion",
        "kaizen_summary",
        "audit_5s_summary",
        "nonconformity_series",
        "ppm_internal_summary",
        "ppm_external_summary",
        "ppm_internal_series",
        "ppm_external_series",
        "lmp_dashboard_summary",
        "lmp_dashboard_charts",
        "transforma_mais_summary",
        "product_sales",
        "quality_branch",
        "hr_branch",
    }
)

LMP_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "lmp",
        "lmp_dashboard",
        "lmp_dashboard_summary",
        "lmp_dashboard_items",
        "lmp_dashboard_charts",
        "transforma_mais_process",
        "transforma_mais_summary",
    }
)

SQL_PRESENT_ENTITIES: frozenset[str] = frozenset({"sql_result"})

SYSTEM_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "protheus_table",
        "protheus_column",
        "protheus_index",
        "protheus_relation",
        "protheus_table_schema",
    }
)

SALE_ORDER_PRESENT_ENTITIES: frozenset[str] = frozenset({"sale_order"})

ENTITY_PATH_HINTS: dict[str, str] = {
    "product_pricing": "/products/0/pricing",
    "product_purchases": "/products/0/purchases",
    "product_suppliers": "/products/0/suppliers",
    "product_customers": "/products/0/customers",
    "product_internal_movements": "/products/0/internal-movements",
    "product_inbound_invoice_items": "/products/0/inbound-invoice-items",
    "product_outbound_invoice_items": "/products/0/outbound-invoice-items",
    "product_sales": "/products/0/sales",
    "product_open_orders": "/products/0/sales/open-orders",
    "product_billing": "/products/0/sales/billing",
    "supplies_cpv": "/supplies/cpv",
    "supplies_otd": "/supplies/otd",
    "supplies_stock_value": "/supplies/stock-value",
    "supplies_inventory_turnover": "/supplies/inventory-turnover",
    "supplies_negotiation_savings": "/supplies/negotiation-savings/summary",
    "financial_rol": "/financial/rol",
    "financial_ebitda_pct": "/financial/ebitda_pct",
    "financial_fixed_cost_pct": "/financial/fixed_cost_pct",
    "financial_pmr": "/financial/pmr",
    "commercial_rol_target": "/commercial/head_office_rol_target_pct",
    "commercial_rol_series": "/commercial/rol/series",
    "sales_conversion_rate": "/commercial/closing-rate",
    "new_clients_average": "/commercial/new-clients-average",
    "sales_order_otd": "/commercial/sales-order-otd",
    "new_business_rol_pct": "/commercial/new-business-rol-pct",
    "new_clients_rol_pct": "/commercial/new-clients-rol-pct",
    "commercial_proposal": "/commercial/proposals",
    "direct_labor_cost_pct": "/production/direct_labor_cost_pct",
    "production_cost_pct": "/production/production_cost_pct",
    "depreciation_pct": "/production/depreciation_pct",
    "production_oee_series": "/production/oee/series",
    "production_otd_series": "/production/otd/series",
    "overall_equipment_effectiveness": "/production/overall_equipment_effectiveness_pct",
    "production_otd": "/production/on_time_delivery_pct",
    "eficiencia_fabril_dashboard": "/production/eficiencia-fabril/dashboard",
    "eficiencia_fabril_appointment": "/production/eficiencia-fabril/appointments",
    "hr_branch": "/hr/branches",
    "hr_snapshot": "/hr/snapshot",
    "hr_active_pdi_count": "/hr/active-pdi-count",
    "hr_performance_reviews_completion": "/hr/performance-reviews-completion",
    "quality_branch": "/quality/branches",
    "nonconformity_series": "/quality/nonconformities/series",
    "kaizen_summary": "/quality/kaizens/summary",
    "audit_5s_summary": "/quality/audit-5s/summary",
    "ppm_internal_summary": "/quality/ppm/internal/summary",
    "ppm_external_summary": "/quality/ppm/external/summary",
    "ppm_internal_series": "/quality/ppm/internal/series",
    "ppm_external_series": "/quality/ppm/external/series",
    "lmp": "/engineering/lmps",
    "lmp_dashboard": "/engineering/lmps/dashboard",
    "lmp_dashboard_summary": "/engineering/lmps/dashboard/summary",
    "lmp_dashboard_items": "/engineering/lmps/dashboard/items",
    "lmp_dashboard_charts": "/engineering/lmps/dashboard/charts",
    "transforma_mais_process": "/engineering/transforma-mais/processes",
    "transforma_mais_summary": "/engineering/transforma-mais/processes/summary",
    "sale_order": "/sales/",
    "sql_result": "/data/sql",
    "protheus_table": "/system/tables/search",
    "protheus_column": "/system/tables/SB1/columns",
    "protheus_index": "/system/tables/SB1/indexes",
    "protheus_relation": "/system/tables/SB1/relations",
    "protheus_table_schema": "/system/tables/SB1/schema",
}

ENTITY_ROUTED_FOR_PRESENT: frozenset[str] = (
    PROFILE_PRESENT_ENTITIES
    | KPI_PRESENT_ENTITIES
    | LMP_PRESENT_ENTITIES
    | SQL_PRESENT_ENTITIES
    | SYSTEM_PRESENT_ENTITIES
    | SALE_ORDER_PRESENT_ENTITIES
    | frozenset({"commercial_proposal", "eficiencia_fabril_appointment"})
)

PATH_ENTITY_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("/analyser", "product_analyser"),
    ("/factory-status", "product_factory_status"),
    ("/structure/exclusivity", "product_structure_exclusivity"),
    ("/exclusive-raw-materials/catalog", "exclusive_raw_materials_catalog"),
    ("/production-status", "product_production_status"),
    ("/shipping-status", "product_shipping_status"),
    ("/raw-material-price-intelligence", "product_raw_material_price_intelligence"),
    ("/cost-impact-simulation", "product_cost_impact_simulation"),
    ("/last-purchase", "product_last_purchase"),
    ("/purchase-price-history", "product_purchase_price_history"),
    ("/purchase-budget-history", "product_purchase_budget_history"),
    ("/structure", "product_structure"),
    ("/parents", "product_parents"),
    ("/stock", "product_stock"),
    ("/guide", "product_guide"),
    ("/inspection", "product_inspection"),
    ("/pricing", "product_pricing"),
    ("/purchases", "product_purchases"),
    ("/suppliers", "product_suppliers"),
    ("/customers", "product_customers"),
    ("/internal-movements", "product_internal_movements"),
    ("/inbound-invoice-items", "product_inbound_invoice_items"),
    ("/outbound-invoice-items", "product_outbound_invoice_items"),
    ("/open-orders", "product_open_orders"),
    ("/sales/billing", "product_billing"),
    ("/sales", "product_sales"),
    ("/summary", "product"),
    ("/search", "product_search"),
    ("/branch_rol_target_pct", "commercial_rol_target"),
    ("/finacial/rol", "financial_rol"),
    ("/finacial/ebitda_pct", "financial_ebitda_pct"),
    ("/finacial/fixed_cost_pct", "financial_fixed_cost_pct"),
    ("/finacial/pmr", "financial_pmr"),
    ("/engineering/lmps/", "lmp"),
    ("/quality/audit-5s/summary", "audit_5s_summary"),
)


@dataclass(frozen=True)
class ApiDelpiResponseProfile:
    entity: str | None
    shape: str | None
    operation_id: str | None
    routed_by: str  # "meta.entity" | "path" | "none"


class ChatApiDelpiResponseProfileService:
    CHAT_CRITICAL_ENTITIES = CHAT_CRITICAL_ENTITIES
    PROFILE_PRESENT_ENTITIES = PROFILE_PRESENT_ENTITIES
    PRODUCT_LIST_PRESENT_ENTITIES = PRODUCT_LIST_PRESENT_ENTITIES
    KPI_PRESENT_ENTITIES = KPI_PRESENT_ENTITIES
    LMP_PRESENT_ENTITIES = LMP_PRESENT_ENTITIES
    SQL_PRESENT_ENTITIES = SQL_PRESENT_ENTITIES
    SYSTEM_PRESENT_ENTITIES = SYSTEM_PRESENT_ENTITIES
    SALE_ORDER_PRESENT_ENTITIES = SALE_ORDER_PRESENT_ENTITIES
    ENTITY_ROUTED_FOR_PRESENT = ENTITY_ROUTED_FOR_PRESENT

    @classmethod
    def resolve(cls, data: Any, *, path: str = "") -> ApiDelpiResponseProfile:
        meta = cls.extract_meta(data)
        entity = None
        shape = None
        operation_id = None
        routed_by = "none"

        if meta:
            raw_entity = meta.get("entity")
            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()
                routed_by = "meta.entity"

            raw_shape = meta.get("shape")
            if isinstance(raw_shape, str) and raw_shape.strip():
                shape = raw_shape.strip()

            raw_operation = meta.get("operationId")
            if isinstance(raw_operation, str) and raw_operation.strip():
                operation_id = raw_operation.strip()

        if not entity:
            fallback_entity = cls._entity_from_path(path)
            if fallback_entity:
                entity = fallback_entity
                routed_by = "path"

        return ApiDelpiResponseProfile(
            entity=entity,
            shape=shape,
            operation_id=operation_id,
            routed_by=routed_by,
        )

    @classmethod
    def extract_meta(cls, data: Any) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None

        meta = data.get("meta")

        if isinstance(meta, dict):
            return meta

        return None

    @classmethod
    def is_chat_critical(cls, entity: str | None) -> bool:
        return bool(entity and entity in CHAT_CRITICAL_ENTITIES)

    @classmethod
    def is_profile_present_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in PROFILE_PRESENT_ENTITIES)

    @classmethod
    def is_kpi_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in KPI_PRESENT_ENTITIES)

    @classmethod
    def is_entity_routed_for_present(cls, entity: str | None) -> bool:
        return bool(entity and entity in ENTITY_ROUTED_FOR_PRESENT)

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        if not entity:
            return ""
        return ENTITY_PATH_HINTS.get(entity, "")

    @classmethod
    def presentation_path(cls, *, path: str = "", entity: str | None = None) -> str:
        normalized = str(path or "").strip()
        if normalized:
            return normalized

        hint = cls.entity_path_hint(entity)
        if not hint:
            return ""

        code_match = re.search(r"/products/(\d+)", normalized, flags=re.IGNORECASE)
        product_code = code_match.group(1) if code_match else "0"
        return hint.replace("/products/0/", f"/products/{product_code}/")

    @classmethod
    def profile_coverage_ratio(cls) -> float:
        if not CHAT_CRITICAL_ENTITIES:
            return 0.0
        covered = CHAT_CRITICAL_ENTITIES & PROFILE_PRESENT_ENTITIES
        return len(covered) / len(CHAT_CRITICAL_ENTITIES)

    @classmethod
    def enrich_humanized(cls, humanized: dict | None, data: Any) -> dict | None:
        return humanized

    @classmethod
    def _entity_from_path(cls, path: str) -> str | None:
        lowered = str(path or "").lower().rstrip("/")

        if not lowered:
            return None

        for entity, hint in ENTITY_PATH_HINTS.items():
            hint_lower = str(hint or "").lower().rstrip("/")

            if not hint_lower:
                continue

            if lowered == hint_lower or lowered.endswith(hint_lower):
                return entity

        for fragment, entity in sorted(
            PATH_ENTITY_FALLBACKS,
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if fragment in lowered:
                return entity

        parts = lowered.rstrip("/").split("/")

        if (
            len(parts) == 3
            and parts[1] == "products"
            and (parts[2].isdigit() or parts[2] in {"{code}", "0"})
        ):
            return "product"

        return None
