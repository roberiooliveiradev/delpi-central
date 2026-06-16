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
