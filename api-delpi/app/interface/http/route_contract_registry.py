"""Contratos semânticos (operationId → entity/shape) para meta do envelope api-delpi."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteContract:
    entity: str
    shape: str


ROUTE_CONTRACTS: dict[str, RouteContract] = {
    # Produtos
    "search_products": RouteContract("product_search", "paged_list"),
    "get_product_detail": RouteContract("product", "product_snapshot"),
    "get_product_summary": RouteContract("product", "product_snapshot"),
    "get_product_structure": RouteContract("product_structure", "hierarchy"),
    "get_product_structure_exclusivity": RouteContract(
        "product_structure_exclusivity", "playbook_report"
    ),
    "get_product_production_status": RouteContract(
        "product_production_status", "playbook_report"
    ),
    "get_product_shipping_status": RouteContract(
        "product_shipping_status", "playbook_report"
    ),
    "get_product_factory_status": RouteContract(
        "product_factory_status", "composite_analysis"
    ),
    "get_product_cost_impact_simulation": RouteContract(
        "product_cost_impact_simulation", "composite_analysis"
    ),
    "get_product_last_purchase": RouteContract(
        "product_last_purchase", "playbook_report"
    ),
    "get_product_purchase_price_history": RouteContract(
        "product_purchase_price_history", "playbook_report"
    ),
    "get_product_purchase_budget_history": RouteContract(
        "product_purchase_budget_history", "playbook_report"
    ),
    "get_product_raw_material_price_intelligence": RouteContract(
        "product_raw_material_price_intelligence", "composite_analysis"
    ),
    "get_product_stock": RouteContract("product_stock", "paged_list"),
    "get_product_analyser": RouteContract("product_analyser", "composite_analysis"),
    "get_product_parents": RouteContract("product_parents", "hierarchy"),
    "get_product_suppliers": RouteContract("product_suppliers", "paged_list"),
    "get_product_customers": RouteContract("product_customers", "paged_list"),
    "get_product_inspection": RouteContract("product_inspection", "paged_list"),
    "get_product_guide": RouteContract("product_guide", "paged_list"),
    "get_product_internal_movements": RouteContract(
        "product_internal_movements", "paged_list"
    ),
    "get_product_inbound_invoice_items": RouteContract(
        "product_inbound_invoice_items", "paged_list"
    ),
    "get_product_outbound_invoice_items": RouteContract(
        "product_outbound_invoice_items", "paged_list"
    ),
    "get_product_purchases": RouteContract("product_purchases", "paged_list"),
    "get_product_sales_summary": RouteContract("product_sales", "scalar"),
    "get_product_sales_open_orders": RouteContract("product_open_orders", "paged_list"),
    "get_product_sales_billing": RouteContract("product_billing", "scalar"),
    "get_product_pricing": RouteContract("product_pricing", "scalar"),
    # Suprimentos
    "get_supplies_cpv": RouteContract("supplies_cpv", "scalar"),
    "get_supplies_otd": RouteContract("supplies_otd", "scalar"),
    "get_supplies_stock_value": RouteContract("supplies_stock_value", "scalar"),
    "get_supplies_inventory_turnover": RouteContract(
        "supplies_inventory_turnover", "scalar"
    ),
    "get_supplies_negotiation_savings_summary": RouteContract(
        "supplies_negotiation_savings", "scalar"
    ),
    # Engenharia
    "list_lmps": RouteContract("lmp", "paged_list"),
    "list_lmps_dashboard": RouteContract("lmp_dashboard", "composite_analysis"),
    "get_lmps_dashboard_summary": RouteContract("lmp_dashboard_summary", "scalar"),
    "list_lmps_dashboard_items": RouteContract("lmp_dashboard_items", "paged_list"),
    "get_lmps_dashboard_charts": RouteContract("lmp_dashboard_charts", "scalar"),
    "get_lmp_by_sale_number": RouteContract("lmp", "product_snapshot"),
    "list_transforma_mais_processes": RouteContract(
        "transforma_mais_process", "paged_list"
    ),
    "get_transforma_mais_summary": RouteContract("transforma_mais_summary", "scalar"),
    # Vendas e dados
    "list_sale_orders": RouteContract("sale_order", "paged_list"),
    "execute_readonly_sql": RouteContract("sql_result", "paged_list"),
    # Financeiro
    "get_financial_rol": RouteContract("financial_rol", "scalar"),
    "get_financial_ebitda_pct": RouteContract("financial_ebitda_pct", "scalar"),
    "get_financial_fixed_cost_pct": RouteContract("financial_fixed_cost_pct", "scalar"),
    "get_financial_pmr": RouteContract("financial_pmr", "scalar"),
    # Comercial
    "get_head_office_rol_target_pct": RouteContract(
        "commercial_rol_target", "scalar"
    ),
    "get_branch_rol_target_pct": RouteContract("commercial_rol_target", "scalar"),
    "get_commercial_rol_series": RouteContract("commercial_rol_series", "scalar"),
    "list_commercial_proposals": RouteContract("commercial_proposal", "paged_list"),
    "get_sales_conversion_rate": RouteContract("sales_conversion_rate", "scalar"),
    "get_new_clients_average": RouteContract("new_clients_average", "scalar"),
    "get_sales_order_otd": RouteContract("sales_order_otd", "scalar"),
    "get_new_business_rol_pct": RouteContract("new_business_rol_pct", "scalar"),
    "get_new_clients_rol_pct": RouteContract("new_clients_rol_pct", "scalar"),
    # Produção
    "get_direct_labor_cost_pct": RouteContract("direct_labor_cost_pct", "scalar"),
    "get_production_cost_pct": RouteContract("production_cost_pct", "scalar"),
    "get_depreciation_pct": RouteContract("depreciation_pct", "scalar"),
    "get_production_oee_series": RouteContract("production_oee_series", "scalar"),
    "get_production_otd_series": RouteContract("production_otd_series", "scalar"),
    "get_overall_equipment_effectiveness_pct": RouteContract(
        "overall_equipment_effectiveness", "scalar"
    ),
    "get_on_time_delivery_pct": RouteContract("production_otd", "scalar"),
    "get_eficiencia_fabril_dashboard": RouteContract(
        "eficiencia_fabril_dashboard", "composite_analysis"
    ),
    "list_pedidos_venda_abertos": RouteContract(
        "open_sales_order", "composite_analysis"
    ),
    "list_ops_abertas_pedidos_venda": RouteContract(
        "open_production_order", "composite_analysis"
    ),
    "list_eficiencia_fabril_appointments": RouteContract(
        "eficiencia_fabril_appointment", "paged_list"
    ),
    # Qualidade (métricas)
    "list_quality_branches": RouteContract("quality_branch", "scalar"),
    "get_nonconformity_series": RouteContract("nonconformity_series", "scalar"),
    "list_nonconformities": RouteContract("nonconformity", "paged_list"),
    "get_kaizen_summary": RouteContract("kaizen_summary", "scalar"),
    "get_audit_5s_summary": RouteContract("audit_5s_summary", "scalar"),
    "get_ppm_internal_summary": RouteContract("ppm_internal_summary", "scalar"),
    "get_ppm_external_summary": RouteContract("ppm_external_summary", "scalar"),
    "get_ppm_internal_series": RouteContract("ppm_internal_series", "scalar"),
    "get_ppm_external_series": RouteContract("ppm_external_series", "scalar"),
    "list_ppm_internal": RouteContract("ppm_internal", "paged_list"),
    "list_ppm_external": RouteContract("ppm_external", "paged_list"),
    "get_produced_quantity": RouteContract("produced_quantity", "playbook_report"),
    # Auditoria 5S operacional
    "list_audit_5s_areas": RouteContract("audit_5s_area", "paged_list"),
    "create_audit_5s_area": RouteContract("audit_5s_area", "scalar"),
    "list_audit_5s_criteria": RouteContract("audit_5s_criterion", "paged_list"),
    "list_audit_5s_audits": RouteContract("audit_5s_audit", "paged_list"),
    "create_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
    "get_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
    "delete_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
    "join_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
    "upsert_audit_5s_response": RouteContract("audit_5s_response", "scalar"),
    "complete_audit_5s_evaluation": RouteContract("audit_5s_audit", "scalar"),
    "list_audit_5s_nc_candidates": RouteContract("audit_5s_nc_candidate", "paged_list"),
    "list_audit_5s_nonconformities": RouteContract("audit_5s_nonconformity", "paged_list"),
    "create_audit_5s_nonconformity": RouteContract("audit_5s_nonconformity", "scalar"),
    "update_audit_5s_nonconformity": RouteContract("audit_5s_nonconformity", "scalar"),
    "list_audit_5s_nc_actions": RouteContract("audit_5s_nc_action", "paged_list"),
    "create_audit_5s_nc_action": RouteContract("audit_5s_nc_action", "scalar"),
    "list_audit_5s_nc_attachments": RouteContract("audit_5s_attachment", "paged_list"),
    "list_audit_5s_audit_nc_attachments": RouteContract(
        "audit_5s_attachment", "paged_list"
    ),
    "attach_audit_5s_evidence": RouteContract("audit_5s_attachment", "scalar"),
    "complete_audit_5s_nc_action": RouteContract("audit_5s_nc_action", "scalar"),
    "get_audit_5s_analytics_dashboard": RouteContract(
        "audit_5s_analytics", "composite_analysis"
    ),
    "close_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
    # RH
    "list_hr_branches": RouteContract("hr_branch", "scalar"),
    "get_hr_snapshot": RouteContract("hr_snapshot", "composite_analysis"),
    "get_hr_active_pdi_count": RouteContract("hr_active_pdi_count", "scalar"),
    "get_hr_performance_reviews_completion": RouteContract(
        "hr_performance_reviews_completion", "scalar"
    ),
    # Agendamento
    "list_scheduling_resources": RouteContract("scheduling_resource", "paged_list"),
    "create_scheduling_resource": RouteContract("scheduling_resource", "scalar"),
    "update_scheduling_resource": RouteContract("scheduling_resource", "scalar"),
    "list_scheduling_bookings": RouteContract("scheduling_booking", "paged_list"),
    "create_scheduling_booking": RouteContract("scheduling_booking", "scalar"),
    "cancel_scheduling_booking": RouteContract("scheduling_booking", "scalar"),
    # Sistema (metadados Protheus)
    "search_tables_by_description": RouteContract("protheus_table", "paged_list"),
    "get_protheus_table": RouteContract("protheus_table", "scalar"),
    "list_protheus_table_columns": RouteContract("protheus_column", "paged_list"),
    "get_protheus_table_indexes": RouteContract("protheus_index", "scalar"),
    "get_protheus_table_relations": RouteContract("protheus_relation", "scalar"),
    "get_protheus_table_schema": RouteContract("protheus_table_schema", "composite_analysis"),
    "search_protheus_columns_in_table": RouteContract("protheus_column", "paged_list"),
    "search_protheus_columns_by_description": RouteContract(
        "protheus_column", "paged_list"
    ),
}


def default_entity(operation_id: str) -> str:
    for prefix in (
        "get_",
        "list_",
        "create_",
        "update_",
        "cancel_",
        "delete_",
        "attach_",
        "complete_",
        "close_",
        "join_",
        "execute_",
        "search_",
        "upsert_",
    ):
        if operation_id.startswith(prefix):
            return operation_id[len(prefix) :]
    return operation_id


def resolve_contract(
    operation_id: str,
    *,
    entity: str | None = None,
    shape: str | None = None,
) -> tuple[str, str]:
    contract = ROUTE_CONTRACTS.get(operation_id)
    resolved_entity = entity or (contract.entity if contract else default_entity(operation_id))
    resolved_shape = shape or (contract.shape if contract else "scalar")
    return resolved_entity, resolved_shape
