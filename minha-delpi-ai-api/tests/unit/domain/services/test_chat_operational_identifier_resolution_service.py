"""Resolução tipada de identificadores operacionais (productCode vs supplierPartNumber)."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_intent_router.chat_intent_router_entity_resolution_service import (
    ChatIntentRouterEntityResolutionService,
)
from app.domain.services.chat_operational_identifier_resolution_service import (
    ChatOperationalIdentifierResolutionService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_supplier_part_number_lookup_predicate_matches_explicit_phrase() -> None:
    normalized = "liste produto com part number do fornecedor 008700056"
    assert OperationalRouteMatcherService.matches_custom_predicate(
        "supplierPartNumberLookup",
        normalized,
    )
    assert not OperationalRouteMatcherService.matches_custom_predicate(
        "suppliersRoute",
        normalized,
    )


def test_resolve_sets_supplier_part_number_not_product_code() -> None:
    resolved = ChatOperationalIdentifierResolutionService.resolve(
        "liste produto com part number do fornecedor 008700056"
    )
    assert resolved.primary is not None
    assert resolved.primary.role == "supplier_part_number"
    assert resolved.primary.value == "008700056"
    assert resolved.ambiguity == "none"


def test_build_resolved_params_uses_supplier_part_number_slot() -> None:
    params = ChatIntentRouterEntityResolutionService.build_resolved_params(
        "liste produto com part number do fornecedor 008700056",
        previous_messages=None,
        memory_entities=None,
    )
    assert params is not None
    assert params.get("supplierPartNumber") == "008700056"
    assert "productCode" not in params


def test_suppliers_of_product_still_resolves_product_code() -> None:
    params = ChatIntentRouterEntityResolutionService.build_resolved_params(
        "liste os fornecedores do produto 10080160",
        previous_messages=None,
        memory_entities=None,
    )
    assert params is not None
    assert params.get("productCode") == "10080160"
    assert "supplierPartNumber" not in params
