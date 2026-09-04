from app.domain.services.chat_operational_pagination_defaults_service import (
    ChatOperationalPaginationDefaultsService,
)


def test_tiers_match_canonical_policy():
    assert ChatOperationalPaginationDefaultsService.standard() == 50
    assert ChatOperationalPaginationDefaultsService.hierarchical() == 500
    assert ChatOperationalPaginationDefaultsService.for_drawing_analyser() == 50


def test_resolve_for_path_uses_hierarchical_markers_from_json():
    assert (
        ChatOperationalPaginationDefaultsService.resolve_for_path(
            "/products/10080022/parents"
        )
        == 500
    )
    assert (
        ChatOperationalPaginationDefaultsService.resolve_for_path(
            "/products/10080022/structure"
        )
        == 500
    )
    assert (
        ChatOperationalPaginationDefaultsService.resolve_for_path("/products/10080022/stock")
        == 50
    )


def test_clamp_requested_respects_cap():
    assert ChatOperationalPaginationDefaultsService.clamp_requested(0) == 1
    assert ChatOperationalPaginationDefaultsService.clamp_requested(120) == 120
    assert ChatOperationalPaginationDefaultsService.clamp_requested(9999) == 500


def test_special_defaults_loaded():
    assert ChatOperationalPaginationDefaultsService.product_search_default() == 5
    assert ChatOperationalPaginationDefaultsService.product_search_message_cap() == 20
    assert ChatOperationalPaginationDefaultsService.exclusive_catalog_limit() == 10
    assert ChatOperationalPaginationDefaultsService.supplies_stock_top_limit() == 10
    assert ChatOperationalPaginationDefaultsService.refinement_context_fallback() == 25
    assert ChatOperationalPaginationDefaultsService.auto_recovery_page_size_cap() == 100
    assert ChatOperationalPaginationDefaultsService.requested_page_size_cap() == 500
    assert ChatOperationalPaginationDefaultsService.agentic_example_page_size() == 50


def test_product_search_limit_uses_canonical_defaults():
    from app.application.services.external_actions.external_action_product_search_route_selection_service import (
        ExternalActionProductSearchRouteSelectionService,
    )

    assert (
        ExternalActionProductSearchRouteSelectionService.extract_search_limit(
            "busque produtos terminais"
        )
        == ChatOperationalPaginationDefaultsService.product_search_default()
    )
    assert (
        ExternalActionProductSearchRouteSelectionService.extract_search_limit(
            "busque 8 produtos terminais"
        )
        == 8
    )
    assert (
        ExternalActionProductSearchRouteSelectionService.extract_search_limit(
            "busque 99 produtos terminais"
        )
        == ChatOperationalPaginationDefaultsService.product_search_message_cap()
    )
