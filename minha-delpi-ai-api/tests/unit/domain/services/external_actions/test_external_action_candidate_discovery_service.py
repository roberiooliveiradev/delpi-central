from app.domain.services.external_actions.external_action_candidate_discovery_service import (
    ExternalActionCandidateDiscoveryService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_candidate_discovery_matches_supplies_kpi_rule():
    rule = ExternalActionCandidateDiscoveryService.match_filter_rule(
        "giro de estoque do mês"
    )
    assert rule is not None
    assert rule["id"] == "suppliesKpi"


def test_candidate_discovery_path_markers_for_production_otd():
    markers = ExternalActionCandidateDiscoveryService.resolve_path_markers(
        "ordens de producao em atraso"
    )
    assert any("otd" in marker or "pcp-orders" in marker for marker in markers)


def test_list_allowed_candidates_merges_marker_actions():
    class _Repo:
        def find_candidate_actions(self, message, limit=8, *, allowed_action_ids=None):
            return [
                {
                    "actionId": "supplies.otd",
                    "path": "/supplies/otd",
                    "operationId": "get_supplies_otd",
                }
            ]

        def list_actions(self):
            return [
                {
                    "actionId": "supplies.otd",
                    "path": "/supplies/otd",
                    "operationId": "get_supplies_otd",
                },
                {
                    "actionId": "prod.otd",
                    "path": "/production/otd",
                    "operationId": "get_production_otd",
                },
                {
                    "actionId": "other",
                    "path": "/quality/nc",
                    "operationId": "list_nc",
                },
            ]

    support = ExternalActionSelectionSupportService(_Repo())
    candidates = support.list_allowed_candidates(
        "ordens de producao em atraso",
        allowed_action_ids=["supplies.otd", "prod.otd", "other"],
        limit=1,
    )
    ids = {item["actionId"] for item in candidates}
    assert "prod.otd" in ids
