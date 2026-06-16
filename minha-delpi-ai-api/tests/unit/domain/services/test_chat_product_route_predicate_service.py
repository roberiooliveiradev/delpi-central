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
