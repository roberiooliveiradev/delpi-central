from app.application.services.external_actions.external_action_candidate_prioritization_service import (
    ExternalActionCandidatePrioritizationService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_supplies_otd_prioritizes_supplies_path_when_domain_terms_match():
    candidates = [
        {"actionId": "prod-otd", "path": "/production/otd"},
        {"actionId": "supplies-otd", "path": "/supplies/otd"},
    ]

    ordered = ExternalActionCandidatePrioritizationService.apply(
        "otd de suprimentos fornecedor",
        candidates,
        supplies_otd=True,
    )

    assert [item["actionId"] for item in ordered] == ["supplies-otd"]


def test_production_otd_detail_prioritizes_detail_route():
    candidates = [
        {"actionId": "generic", "path": "/production/dashboard"},
        {
            "actionId": "detail",
            "path": "/production/otd",
            "operationId": "get_production_otd",
        },
    ]

    ordered = ExternalActionCandidatePrioritizationService.apply(
        "listar ordens de producao ops atrasadas",
        candidates,
    )

    assert ordered[0]["actionId"] == "detail"


def test_production_pcp_late_ops_prioritizes_pcp_over_commercial():
    candidates = [
        {
            "actionId": "commercial-rol",
            "path": "/commercial/branch_rol_target_pct",
            "operationId": "get_commercial_branch_rol_target_pct",
            "summary": "Indicador — Meta percentual rol comercial",
        },
        {
            "actionId": "pcp-items",
            "path": "/production/pcp-orders/items",
            "operationId": "get_production_pcp_orders_items",
            "summary": "Itens de OPs PCP",
        },
        {
            "actionId": "pcp-ranking",
            "path": "/production/pcp-orders/ranking",
            "operationId": "get_production_pcp_orders_ranking",
            "summary": "Ranking de OPs PCP",
        },
    ]

    ordered = ExternalActionCandidatePrioritizationService.apply(
        "ops em atraso pcp",
        candidates,
    )

    assert all("pcp" in str(item.get("path") or "").lower() for item in ordered)
    assert ordered[0]["operationId"] == "get_production_pcp_orders_items"
    assert "commercial" not in str(ordered[0].get("path") or "").lower()


def test_production_otd_matches_atraso_without_atrasad_stem():
    candidates = [
        {"actionId": "commercial", "path": "/commercial/rol"},
        {
            "actionId": "otd",
            "path": "/production/otd",
            "operationId": "get_production_otd",
        },
    ]

    ordered = ExternalActionCandidatePrioritizationService.apply(
        "ops em atraso na producao",
        candidates,
    )

    assert ordered[0]["actionId"] == "otd"
