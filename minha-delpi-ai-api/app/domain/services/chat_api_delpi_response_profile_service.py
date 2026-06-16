"""Roteamento de apresentação por meta.entity (contrato OpenAPI operacional)."""

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
        "production_consumption_top_items",
        "production_losses_top_materials",
        "production_losses_records",
        "production_schedule_today",
        "production_orders_open",
        "production_orders_finished",
        "production_work_center_order_summary",
        "production_consumption_top_items_by_work_center",
        "production_consumption_top_items_validated",
        "production_allocation_gaps",
        "production_orders_finished_without_consumption",
        "production_work_center_average_planned_time",
        "production_consumption_by_item",
        "production_planned_vs_real_time",
        "purchases_top_products",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_raw_material_price_intelligence",
        "product_cost_impact_simulation",
        "product_last_purchase",
        "product_purchase_price_history",
        "product_purchase_budget_history",
        "product_directives",
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

PLAYBOOK_OPERATIONAL_ENTITIES: frozenset[str] = frozenset(
    {
        "production_consumption_top_items",
        "production_losses_top_materials",
        "production_losses_records",
        "production_schedule_today",
        "production_orders_open",
        "production_orders_finished",
        "production_work_center_order_summary",
        "production_consumption_top_items_by_work_center",
        "production_consumption_top_items_validated",
        "production_allocation_gaps",
        "production_orders_finished_without_consumption",
        "production_work_center_average_planned_time",
        "production_consumption_by_item",
        "production_planned_vs_real_time",
        "purchases_top_products",
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
        "production_consumption_top_items",
        "production_losses_top_materials",
        "production_losses_records",
        "production_schedule_today",
        "production_orders_open",
        "production_orders_finished",
        "production_work_center_order_summary",
        "production_consumption_top_items_by_work_center",
        "production_consumption_top_items_validated",
        "production_allocation_gaps",
        "production_orders_finished_without_consumption",
        "production_work_center_average_planned_time",
        "production_consumption_by_item",
        "production_planned_vs_real_time",
        "purchases_top_products",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_raw_material_price_intelligence",
        "product_cost_impact_simulation",
        "product_last_purchase",
        "product_purchase_price_history",
        "product_purchase_budget_history",
        "product_directives",
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
        "production_oee_detail",
        "production_oee_appointment",
        "production_otd_series",
        "overall_equipment_effectiveness",
        "production_otd",
        "production_otd_detail",
        "eficiencia_fabril_dashboard",
        "hr_snapshot",
        "hr_active_pdi_count",
        "hr_performance_reviews_completion",
        "kaizen_summary",
        "kaizen",
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

ENTITY_ROUTED_FOR_PRESENT: frozenset[str] = (
    PROFILE_PRESENT_ENTITIES
    | KPI_PRESENT_ENTITIES
    | LMP_PRESENT_ENTITIES
    | SQL_PRESENT_ENTITIES
    | SYSTEM_PRESENT_ENTITIES
    | SALE_ORDER_PRESENT_ENTITIES
    | frozenset({"commercial_proposal", "eficiencia_fabril_appointment"})
)


@dataclass(frozen=True)
class ApiDelpiResponseProfile:
    entity: str | None
    shape: str | None
    operation_id: str | None
    routed_by: str  # "meta.entity" | "path" | "none"


class ChatApiDelpiResponseProfileService:
    CHAT_CRITICAL_ENTITIES = CHAT_CRITICAL_ENTITIES
    PLAYBOOK_OPERATIONAL_ENTITIES = PLAYBOOK_OPERATIONAL_ENTITIES
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
    def is_playbook_operational_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in PLAYBOOK_OPERATIONAL_ENTITIES)

    @classmethod
    def resolve_entity_from_path(cls, path: str) -> str | None:
        return cls._entity_from_path(path)

    @classmethod
    def is_playbook_operational_path(cls, path: str) -> bool:
        entity = cls._entity_from_path(path)
        return cls.is_playbook_operational_entity(entity)

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_path_hint(entity)

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
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.resolve_entity_from_path(path)
