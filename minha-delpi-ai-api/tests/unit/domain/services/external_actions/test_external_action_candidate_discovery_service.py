from app.domain.services.external_actions.external_action_candidate_discovery_service import (
    ExternalActionCandidateDiscoveryService,
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


def test_candidate_discovery_product_terms_with_clean_descricao():
    rule = ExternalActionCandidateDiscoveryService.match_filter_rule(
        "qual a descrição do 10050078?"
    )
    assert rule is not None
    assert rule["id"] == "productTerms"


def test_candidate_discovery_product_terms_with_descriao_typo():
    """Typo descrião: normalize_for_matching deve casar productTerms."""
    rule = ExternalActionCandidateDiscoveryService.match_filter_rule(
        "qual a descrião do 10050078?"
    )
    assert rule is not None
    assert rule["id"] == "productTerms"


def test_candidate_discovery_how_to_describe_does_not_match_product_terms():
    rule = ExternalActionCandidateDiscoveryService.match_filter_rule(
        "como descrever um terminal?"
    )
    assert rule is None or rule["id"] != "productTerms"
