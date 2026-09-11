"""J-R9 — semantic single owner: Action Catalog owns action selection."""

from __future__ import annotations

from app.application.services.external_actions.operational_route_selection.operational_route_domain_selection_service import (
    OperationalRouteDomainSelectionService,
)
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.chat_semantic_authority_ownership_service import (
    ChatSemanticAuthorityOwnershipService,
)
from app.domain.services.turn_understanding_kpi_intent_mapper_service import (
    TurnUnderstandingKpiIntentMapperService,
)
from app.domain.services.turn_understanding_product_intent_mapper_service import (
    TurnUnderstandingProductIntentMapperService,
)
from app.domain.services.turn_understanding_production_intent_mapper_service import (
    TurnUnderstandingProductionIntentMapperService,
)


def test_j_r9_ownership_matrix_action_catalog_is_single_owner():
    matrix = ChatSemanticAuthorityOwnershipService.ownership_matrix()
    assert matrix["actionSelection"] == "openapi_action_catalog"
    assert matrix["familyMappersRole"] == "removed_as_selection_authority"
    assert ChatSemanticAuthorityOwnershipService.family_mapper_may_select_route() is False
    assert ChatSemanticAuthorityOwnershipService.family_intent_resolve_enabled() is False


def test_j_r9_token_rules_emptied_on_family_mappers():
    assert TurnUnderstandingKpiIntentMapperService._TOKEN_RULES == ()
    assert TurnUnderstandingProductIntentMapperService._TOKEN_RULES == ()
    assert TurnUnderstandingProductionIntentMapperService._TOKEN_RULES == ()


def test_j_r9_positive_kpi_prose_does_not_resolve_catalog_token():
    assert ChatDepartmentKpiIntentService.resolve("taxa de conversão comercial") is None
    assert TurnUnderstandingKpiIntentMapperService.from_message("rol por filial") is None


def test_j_r9_sibling_production_prose_does_not_resolve_kind():
    assert ChatProductionOperationalIntentService.resolve("ops abertas hoje") is None
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message("programação de produção")
        is None
    )


def test_j_r9_negative_force_legacy_still_available_for_parity_tests():
    legacy = ChatDepartmentKpiIntentService.resolve(
        "taxa de conversão comercial",
        force_legacy=True,
    )
    assert legacy is not None
    assert legacy.path_token


def test_j_r9_domain_selectors_return_none_without_catalog_authority():
    service = OperationalRouteDomainSelectionService(
        catalog=None,
        resolver=None,
        vocabulary=None,
    )
    assert service.select_by_department_kpi("rol comercial", []) is None
    assert service.select_by_intent("estoque", "12345", "stock", []) is None
    assert service.select_production_operational("ops abertas", allowed_action_ids=[]) is None


def test_j_r9_product_mapper_does_not_emit_facet_from_prose():
    assert TurnUnderstandingProductIntentMapperService.from_goal_prose("estoque do produto") is None
