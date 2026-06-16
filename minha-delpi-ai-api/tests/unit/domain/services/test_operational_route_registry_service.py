from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_operational_route_registry_loads_p0_routes() -> None:
    assert OperationalRouteRegistryService.version() == "2026.06.4"
    assert "vocabularyFastPaths" in OperationalRouteRegistryService.dispatch_order()

    route_ids = OperationalRouteRegistryService.route_ids()

    assert "productDirectives" in route_ids
    assert "productFactoryStatus" in route_ids
    assert "exclusiveRawMaterialCatalog" in route_ids
    assert "productionConsumptionTopItems" in route_ids
    assert "commercialSaleOrders" in route_ids
    assert "systemTablesSearch" in route_ids
    assert len(route_ids) >= 35


def test_operational_route_registry_production_operational_kind_lookup() -> None:
    route = OperationalRouteRegistryService.route_by_production_operational_kind(
        "lossesTop"
    )

    assert route is not None
    assert route["id"] == "productionLossesTopMaterials"


def test_operational_route_registry_has_intent_bound_routes() -> None:
    bindings = {
        str(route.get("intentBinding") or "").strip().lower()
        for route in OperationalRouteRegistryService.intent_bound_routes()
    }

    assert "stock" in bindings
    assert "structure" in bindings
    assert "parents" in bindings
    assert "summary" in bindings


def test_operational_route_registry_routes_sorted_by_priority() -> None:
    routes = OperationalRouteRegistryService.routes()
    priorities = [int(route.get("priority") or 0) for route in routes]

    assert priorities == sorted(priorities, reverse=True)
    assert routes[0]["id"] == "productDirectives"


def test_operational_route_matcher_terms_from() -> None:
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "ultima compra do produto 10080001"
    )

    assert OperationalRouteMatcherService.matches(
        {
            "allOf": [
                {"termsFrom": "product_query_intent.lastPurchase.terms"},
                {"hasProductIdentifier": True},
            ]
        },
        message="ultima compra do produto 10080001",
        normalized=normalized,
    )


def test_operational_route_matcher_none_of_excludes_directives() -> None:
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "diretivas 90260882"
    )

    assert OperationalRouteMatcherService.matches(
        {"customPredicate": "directives"},
        message="diretivas 90260882",
        normalized=normalized,
    )

    assert not OperationalRouteMatcherService.matches(
        {
            "allOf": [{"termsFrom": "product_query_intent.lastPurchase.terms"}],
            "noneOf": [{"termsFrom": "product_query_intent.directives.terms"}],
        },
        message="diretivas 90260882",
        normalized=normalized,
    )


def test_operational_route_matcher_factory_status_predicate() -> None:
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "Qual o status completo na fábrica do produto 90269002 hoje?"
    )

    assert OperationalRouteMatcherService.matches(
        {"customPredicate": "factoryStatus"},
        message="Qual o status completo na fábrica do produto 90269002 hoje?",
        normalized=normalized,
    )
