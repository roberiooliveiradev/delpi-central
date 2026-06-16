from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_route_predicate_service import (
    ChatProductRoutePredicateService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


def test_registered_route_predicates_include_product_routes():
    predicates = ChatProductRoutePredicateService.registered_predicates()

    assert "purchasesRoute" in predicates
    assert "productSummaryRoute" in predicates
    assert "genericInvoiceRoute" in predicates


def test_purchases_route_excludes_last_purchase_playbook():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "ultima compra do produto 10080001"
    )

    assert not ChatProductRoutePredicateService.matches("purchasesRoute", normalized)
    assert ChatProductRoutePredicateService.matches(
        "purchasesRoute",
        ChatMessageNormalizationService.normalize_for_matching(
            "historico de compras do produto 10080001"
        ),
    )


def test_product_summary_route_any_of_branches():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "resumo do produto 10080001"
    )

    assert ChatProductRoutePredicateService.matches("productSummaryRoute", normalized)

    assert not ChatProductRoutePredicateService.matches(
        "productSummaryRoute",
        ChatMessageNormalizationService.normalize_for_matching(
            "resumo kaizen do produto 10080001"
        ),
    )


def test_matcher_resolves_route_predicates_from_registry():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "roteiro do produto 90260142"
    )

    assert OperationalRouteMatcherService.matches_custom_predicate(
        "guideRoute",
        normalized,
    )


def test_playbook_predicates_include_directives_and_production():
    predicates = ChatProductRoutePredicateService.registered_predicates()

    assert "directives" in predicates
    assert "productionStatus" in predicates
    assert "lastPurchase" in predicates


def test_directives_playbook_predicate_requires_product_scope():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "diretivas do produto 90260142"
    )

    assert ChatProductRoutePredicateService.matches("directives", normalized)

    assert not ChatProductRoutePredicateService.matches(
        "directives",
        ChatMessageNormalizationService.normalize_for_matching("diretivas em geral"),
    )


def test_factory_status_excludes_production_apontamento():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "O produto 90269002 já tem apontamento na OP?"
    )

    assert not ChatProductRoutePredicateService.matches("factoryStatus", normalized)
    assert ChatProductRoutePredicateService.matches("productionStatus", normalized)


def test_shipping_status_matches_expedicao_with_product_scope():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "Quanto do produto 90269002 já foi liberado para expedição?"
    )

    assert ChatProductRoutePredicateService.matches("shippingStatus", normalized)
