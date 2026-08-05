"""Cobertura de operationIds — consolidação CAPEX (Fase 2D.1).

Mantém menção textual dos operationIds para o inventário de cobertura de rotas.
"""

OPERATION_IDS = [
    "get_planejamento_orcamentario_capex_consolidation_summary",
    "list_planejamento_orcamentario_capex_consolidation_by_unit",
    "list_planejamento_orcamentario_capex_consolidation_by_area",
    "list_planejamento_orcamentario_capex_consolidation_by_cost_center",
    "list_planejamento_orcamentario_capex_consolidation_by_category",
    "list_planejamento_orcamentario_capex_consolidation_by_priority",
    "list_planejamento_orcamentario_capex_consolidation_by_origin",
    "list_planejamento_orcamentario_capex_consolidation_by_month",
    "list_planejamento_orcamentario_capex_consolidation_by_plan_status",
    "list_planejamento_orcamentario_capex_consolidation_details",
    "export_planejamento_orcamentario_capex_consolidation_xlsx",
]


def test_capex_consolidation_operation_ids_registered():
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    for op in OPERATION_IDS:
        assert op in ROUTE_CONTRACTS, f"operationId ausente no registry: {op}"
        assert ROUTE_CONTRACTS[op].entity == "capex_consolidation"
