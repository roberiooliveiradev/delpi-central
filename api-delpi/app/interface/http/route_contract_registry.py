"""Contratos semânticos (operationId → entity/shape) para meta do envelope api-delpi."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteContract:
    entity: str
    shape: str


# Playbook 22 Fase D — stack rico só onde OpenAPI declara strategy enriched.
ENRICHED_PRESENTATION_ENTITIES = frozenset(
    {
        "product_analyser",
        "product_stock",
        "product_structure",
        "product_parents",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_structure_exclusivity",
        "product_raw_material_price_intelligence",
        "product_cost_impact_simulation",
        "product_last_purchase",
        "product_directives",
        "product_purchase_price_history",
        "product_purchase_budget_history",
        "product_pricing",
        "product_purchases",
    }
)


def presentation_strategy_for_entity(entity: str | None) -> str:
    token = str(entity or "").strip()

    if token in ENRICHED_PRESENTATION_ENTITIES:
        return "enriched"

    return "as_delivered"


ROUTE_CONTRACTS: dict[str, RouteContract] = {
    # Produtos
    "search_products": RouteContract("product_search", "paged_list"),
    "get_product_detail": RouteContract("product", "product_snapshot"),
    "get_product_summary": RouteContract("product", "product_snapshot"),
    "get_product_structure": RouteContract("product_structure", "hierarchy"),
    "get_product_structure_exclusivity": RouteContract(
        "product_structure_exclusivity", "playbook_report"
    ),
    "list_exclusive_raw_materials_catalog": RouteContract(
        "exclusive_raw_materials_catalog", "playbook_report"
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
    "get_product_directives": RouteContract(
        "product_directives", "composite_analysis"
    ),
    "get_product_stock": RouteContract("product_stock", "paged_list"),
    "get_product_analyser": RouteContract("product_analyser", "composite_analysis"),
    "get_product_drawing": RouteContract("product_drawing", "scalar"),
    "get_product_drawing_pdf": RouteContract("product_drawing", "document_export"),
    "list_product_drawings": RouteContract("product_drawing_catalog", "paged_list"),
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
    "get_dashboard_department_idd": RouteContract("dashboard_department_idd", "scalar"),
    "get_lmp_by_sale_number": RouteContract("lmp", "product_snapshot"),
    "get_lmp_history_events": RouteContract("lmp_history", "paged_list"),
    "get_lmp_history_flow": RouteContract("lmp_history_flow", "list"),
    "list_transforma_mais_processes": RouteContract(
        "transforma_mais_process", "paged_list"
    ),
    "get_transforma_mais_summary": RouteContract("transforma_mais_summary", "scalar"),
    "list_mini_applicators_ferramentas": RouteContract(
        "mini_applicators_ferramenta", "paged_list"
    ),
    "get_mini_applicators_ferramenta": RouteContract(
        "mini_applicators_ferramenta", "scalar"
    ),
    "list_mini_applicators_pecas": RouteContract("mini_applicators_peca", "list"),
    "get_mini_applicators_golpes": RouteContract("mini_applicators_golpes", "scalar"),
    "list_mini_applicators_componentes": RouteContract("mini_applicators_componente", "list"),
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
    "get_commercial_proposal": RouteContract("commercial_proposal", "product_snapshot"),
    "get_commercial_proposal_history_events": RouteContract(
        "commercial_proposal_history", "paged_list"
    ),
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
    "get_production_oee": RouteContract("production_oee_detail", "paged_list"),
    "get_production_oee_appointment_by_id": RouteContract(
        "production_oee_appointment",
        "composite_analysis",
    ),
    "get_production_otd_series": RouteContract("production_otd_series", "scalar"),
    "get_overall_equipment_effectiveness_pct": RouteContract(
        "overall_equipment_effectiveness", "scalar"
    ),
    "get_on_time_delivery_pct": RouteContract("production_otd", "scalar"),
    "get_production_otd": RouteContract("production_otd", "paged_list"),
    "get_production_consumption_top_items": RouteContract(
        "production_consumption_top_items", "playbook_report"
    ),
    "get_production_losses_records": RouteContract(
        "production_losses_records", "playbook_report"
    ),
    "get_production_losses_top_materials": RouteContract(
        "production_losses_top_materials", "playbook_report"
    ),
    "get_production_schedule_today": RouteContract(
        "production_schedule_today", "playbook_report"
    ),
    "get_production_orders_open": RouteContract(
        "production_orders_open", "playbook_report"
    ),
    "get_production_order_by_op": RouteContract(
        "production_order_detail", "playbook_report"
    ),
    "get_production_orders_finished": RouteContract(
        "production_orders_finished", "playbook_report"
    ),
    "get_production_work_center_order_summary": RouteContract(
        "production_work_center_order_summary", "playbook_report"
    ),
    "get_production_consumption_top_items_by_work_center": RouteContract(
        "production_consumption_top_items_by_work_center", "playbook_report"
    ),
    "get_production_consumption_top_items_validated": RouteContract(
        "production_consumption_top_items_validated", "playbook_report"
    ),
    "get_production_allocation_gaps": RouteContract(
        "production_allocation_gaps", "playbook_report"
    ),
    "get_production_orders_finished_without_consumption": RouteContract(
        "production_orders_finished_without_consumption", "playbook_report"
    ),
    "get_production_work_center_average_planned_time": RouteContract(
        "production_work_center_average_planned_time", "playbook_report"
    ),
    "get_production_consumption_by_item": RouteContract(
        "production_consumption_by_item", "playbook_report"
    ),
    "get_production_planned_vs_real_time": RouteContract(
        "production_planned_vs_real_time", "playbook_report"
    ),
    "get_purchases_top_products": RouteContract(
        "purchases_top_products", "playbook_report"
    ),
    "get_eficiencia_fabril_dashboard": RouteContract(
        "eficiencia_fabril_dashboard", "composite_analysis"
    ),
    "get_inspecoes_entrada_resumo": RouteContract(
        "inspecoes_entrada_resumo", "scalar"
    ),
    "get_inspecoes_entrada_pendentes": RouteContract(
        "inspecoes_entrada_pendentes", "paged_list"
    ),
    "get_inspecoes_entrada_pendentes_fornecedor": RouteContract(
        "inspecoes_entrada_pendentes_fornecedor", "list"
    ),
    "get_inspecoes_entrada_rejeitadas_ensaiador": RouteContract(
        "inspecoes_entrada_rejeitadas_ensaiador", "list"
    ),
    "get_inspecoes_entrada_rejeitadas_produto": RouteContract(
        "inspecoes_entrada_rejeitadas_produto", "list"
    ),
    "get_inspecoes_entrada_historico": RouteContract(
        "inspecoes_entrada_historico", "paged_list"
    ),
    "get_inspecoes_entrada_historico_detalhe": RouteContract(
        "inspecoes_entrada_historico_detalhe", "object"
    ),
    "search_quality_label_ops": RouteContract("quality_label_op_suggestion", "object"),
    "lookup_quality_label_op": RouteContract("quality_label_op_lookup", "scalar"),
    "create_quality_label": RouteContract("quality_label", "scalar"),
    "list_quality_labels": RouteContract("quality_label", "paged_list"),
    "get_quality_label": RouteContract("quality_label", "scalar"),
    "set_quality_label_active": RouteContract("quality_label", "scalar"),
    "delete_quality_label": RouteContract("quality_label", "scalar"),
    "list_quality_label_audit_events": RouteContract(
        "quality_label_audit_event", "paged_list"
    ),
    "list_quality_label_checklist_template": RouteContract(
        "quality_label_checklist_item", "object"
    ),
    "get_quality_label_inspector": RouteContract("quality_label_inspector", "scalar"),
    "save_quality_label_inspector": RouteContract("quality_label_inspector", "scalar"),
    "upload_quality_label_inspector_signature": RouteContract(
        "quality_label_inspector", "scalar"
    ),
    "get_quality_label_certificate": RouteContract("quality_label_certificate", "scalar"),
    "save_quality_label_certificate": RouteContract("quality_label_certificate", "scalar"),
    "get_public_quality_label_inspection": RouteContract(
        "quality_label_public_inspection", "scalar"
    ),
    "list_pedidos_venda_abertos": RouteContract(
        "open_sales_order", "composite_analysis"
    ),
    "list_ops_abertas_pedidos_venda": RouteContract(
        "open_production_order", "composite_analysis"
    ),
    "list_propostas_comerciais": RouteContract(
        "commercial_proposal_document", "paged_list"
    ),
    "get_proposta_comercial": RouteContract(
        "commercial_proposal_document", "composite_analysis"
    ),
    "export_proposta_comercial_pdf": RouteContract(
        "commercial_proposal_document", "document_export"
    ),
    "list_eficiencia_fabril_appointments": RouteContract(
        "eficiencia_fabril_appointment", "paged_list"
    ),
    # Qualidade (métricas)
    "list_quality_branches": RouteContract("quality_branch", "scalar"),
    "get_nonconformity_series": RouteContract("nonconformity_series", "scalar"),
    "list_nonconformities": RouteContract("nonconformity", "paged_list"),
    "get_kaizen_summary": RouteContract("kaizen_summary", "scalar"),
    "get_kaizen_by_id": RouteContract("kaizen", "scalar"),
    "get_kaizen_records_summary": RouteContract("kaizen_records_summary", "scalar"),
    "list_kaizen_records": RouteContract("kaizen_record", "paged_list"),
    "create_kaizen_record": RouteContract("kaizen_record", "scalar"),
    "get_kaizen_record": RouteContract("kaizen_record", "scalar"),
    "update_kaizen_record": RouteContract("kaizen_record", "scalar"),
    "delete_kaizen_record": RouteContract("kaizen_record", "scalar"),
    "export_kaizen_records": RouteContract("kaizen_record_export", "scalar"),
    "import_kaizen_records": RouteContract("kaizen_record_import", "scalar"),
    "list_kaizen_revisions": RouteContract("kaizen_revision", "paged_list"),
    "get_kaizen_revision": RouteContract("kaizen_revision", "scalar"),
    "get_kaizen_at_date": RouteContract("kaizen_revision", "scalar"),
    "create_kaizen_version": RouteContract("kaizen_revision", "scalar"),
    "update_kaizen_version": RouteContract("kaizen_revision", "scalar"),
    "delete_kaizen_version": RouteContract("kaizen_revision", "scalar"),
    "implement_kaizen_version": RouteContract("kaizen_record", "scalar"),
    "list_kaizen_history": RouteContract("kaizen_history", "paged_list"),
    "list_kaizen_audit_log": RouteContract("kaizen_audit_log", "paged_list"),
    "get_kaizen_savings_timeline": RouteContract("kaizen_savings_timeline", "scalar"),
    "list_kaizen_evidences": RouteContract("kaizen_evidence", "paged_list"),
    "attach_kaizen_evidence": RouteContract("kaizen_evidence", "scalar"),
    "update_kaizen_evidence": RouteContract("kaizen_evidence", "scalar"),
    "delete_kaizen_evidence": RouteContract("kaizen_evidence", "scalar"),
    "get_quality_action_plans_dashboard": RouteContract(
        "quality_action_plan_dashboard", "scalar"
    ),
    "dispatch_quality_action_plan_notifications": RouteContract(
        "quality_action_plan_notifications", "scalar"
    ),
    "list_quality_action_plans_overdue": RouteContract(
        "quality_action_plan", "paged_list"
    ),
    "list_quality_action_plans_recurrence": RouteContract(
        "quality_action_plan_recurrence", "paged_list"
    ),
    "list_quality_action_plan_my_queue": RouteContract(
        "quality_action_plan_action", "paged_list"
    ),
    "list_quality_action_plan_assignable_users": RouteContract(
        "directory_user", "paged_list"
    ),
    "list_quality_action_plans": RouteContract("quality_action_plan", "paged_list"),
    "get_quality_action_plan_detail": RouteContract(
        "quality_action_plan", "composite_analysis"
    ),
    "create_quality_action_plan": RouteContract("quality_action_plan", "scalar"),
    "update_quality_action_plan": RouteContract("quality_action_plan", "scalar"),
    "delete_quality_action_plan": RouteContract("quality_action_plan", "scalar"),
    "update_quality_action_plan_status": RouteContract("quality_action_plan", "scalar"),
    "reopen_quality_action_plan": RouteContract("quality_action_plan", "scalar"),
    "upsert_quality_action_plan_ishikawa": RouteContract("quality_action_plan_ishikawa", "scalar"),
    "upsert_quality_action_plan_five_whys": RouteContract("quality_action_plan_five_whys", "scalar"),
    "create_quality_action_plan_actions": RouteContract("quality_action_plan_action", "paged_list"),
    "update_quality_action_plan_action": RouteContract("quality_action_plan_action", "scalar"),
    "delete_quality_action_plan_action": RouteContract("quality_action_plan_action", "scalar"),
    "record_quality_action_plan_effectiveness": RouteContract("quality_action_plan", "scalar"),
    "submit_quality_action_plan_effectiveness_review": RouteContract(
        "quality_action_plan", "scalar"
    ),
    "approve_quality_action_plan_effectiveness_review": RouteContract(
        "quality_action_plan", "scalar"
    ),
    "reject_quality_action_plan_effectiveness_review": RouteContract(
        "quality_action_plan", "scalar"
    ),
    "list_quality_action_plan_pending_effectiveness_reviews": RouteContract(
        "quality_action_plan", "paged_list"
    ),
    "list_quality_action_plan_audit_log": RouteContract(
        "quality_action_plan_audit_log", "paged_list"
    ),
    "list_quality_action_plan_revisions": RouteContract(
        "quality_action_plan_revision", "paged_list"
    ),
    "get_quality_action_plan_revision": RouteContract(
        "quality_action_plan_revision", "composite_analysis"
    ),
    "restore_quality_action_plan_revision": RouteContract(
        "quality_action_plan", "composite_analysis"
    ),
    "upsert_quality_action_plan_rnc_8d": RouteContract("quality_action_plan", "composite_analysis"),
    "list_quality_action_plan_export_templates": RouteContract(
        "quality_action_plan_export_template", "paged_list"
    ),
    "export_quality_action_plan_rnc_8d": RouteContract("quality_action_plan_export", "scalar"),
    "export_quality_action_plan_pdf": RouteContract("quality_action_plan_export", "document_export"),
    "export_quality_action_plan_rnc_8d_pdf": RouteContract(
        "quality_action_plan_export", "document_export"
    ),
    "list_quality_action_plan_evidences": RouteContract("quality_action_plan_evidence", "paged_list"),
    "search_quality_action_plan_evidences": RouteContract(
        "quality_action_plan_evidence", "paged_list"
    ),
    "attach_quality_action_plan_evidence": RouteContract("quality_action_plan_evidence", "scalar"),
    "download_quality_action_plan_evidence": RouteContract("quality_action_plan_evidence", "document_export"),
    "get_quality_action_plan_evidence_content": RouteContract("quality_action_plan_evidence", "composite_analysis"),
    "update_quality_action_plan_evidence": RouteContract("quality_action_plan_evidence", "scalar"),
    "delete_quality_action_plan_evidence": RouteContract("quality_action_plan_evidence", "scalar"),
    "get_quality_action_plan_similar_cases": RouteContract(
        "quality_action_plan_similar_cases", "composite_analysis"
    ),
    "assess_quality_action_plan_recurrence_on_opening": RouteContract(
        "quality_action_plan_recurrence_opening_assessment",
        "composite_analysis",
    ),
    "get_quality_action_plan_knowledge_graph": RouteContract(
        "quality_action_plan_knowledge_graph",
        "composite_analysis",
    ),
    "suggest_quality_action_plan_evidence_tags": RouteContract(
        "quality_action_plan_evidence_tag_suggestions",
        "composite_analysis",
    ),
    "suggest_quality_action_plan_evidence_tags_from_image": RouteContract(
        "quality_action_plan_evidence_tag_suggestions",
        "composite_analysis",
    ),
    "list_quality_solution_patterns": RouteContract(
        "quality_solution_pattern", "paged_list"
    ),
    "promote_quality_action_plan_solution_pattern": RouteContract(
        "quality_solution_pattern", "scalar"
    ),
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
    "update_audit_5s_audit": RouteContract("audit_5s_audit", "scalar"),
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
    "create_scheduling_recurring_booking": RouteContract("scheduling_booking", "composite_analysis"),
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
