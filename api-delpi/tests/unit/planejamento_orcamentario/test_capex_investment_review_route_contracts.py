"""Cobertura de operationIds — decisão CAPEX por investimento."""

OPERATION_IDS = [
    "approve_planejamento_orcamentario_capex_investment",
    "reject_planejamento_orcamentario_capex_investment",
]


def test_capex_investment_review_operation_ids_registered():
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    for op in OPERATION_IDS:
        assert op in ROUTE_CONTRACTS, f"operationId ausente no registry: {op}"
        assert ROUTE_CONTRACTS[op].entity == "capex_plan"
