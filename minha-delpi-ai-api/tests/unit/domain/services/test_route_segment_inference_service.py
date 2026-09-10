"""E9.S12.D — routeSegment inference from OpenAPI operationIds."""

from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)
from app.domain.services.route_segment_inference_service import (
    RouteSegmentInferenceService,
)


def test_continuity_keys_from_nested_and_aliased_paths() -> None:
    assert "open-orders" in RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/{code}/sales/open-orders"
    )
    assert "inbound-invoice" in RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/{code}/inbound-invoice-items"
    )
    assert "directives" in RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/directives/{identifier}"
    )
    assert "by-supplier-part-number" in RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/by-supplier-part-number"
    )
    # Negative: nested structure facet must not collide with base structure.
    exclusivity_keys = RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/{code}/structure/exclusivity"
    )
    assert "structure/exclusivity" in exclusivity_keys
    assert "structure" not in exclusivity_keys


def test_routes_by_segment_without_registry_route_segment_field() -> None:
    for route in OperationalRouteRegistryService.routes():
        assert "routeSegment" not in route

    guide = OperationalRouteRegistryService.routes_by_segment("guide")
    assert guide
    assert guide[0]["id"] == "productGuide"

    open_orders = OperationalRouteRegistryService.routes_by_segment("open-orders")
    assert any(route["id"] == "productOpenOrders" for route in open_orders)

    inbound = OperationalRouteRegistryService.routes_by_segment("inbound-invoice")
    assert any(route["id"] == "productInvoicesInbound" for route in inbound)


def test_refinement_intent_map_still_covers_stock_structure_parents() -> None:
    mapping = OperationalRouteRegistryService.refinement_intent_by_route_segment()
    assert mapping["stock"] == "stock"
    assert mapping["structure"] == "structure"
    assert mapping["parents"] == "parents"


def test_shipping_status_derived_from_operation_ids() -> None:
    # Sibling: routes without legacy routeSegment still resolve via OpenAPI path-tail.
    shipping = OperationalRouteRegistryService.routes_by_segment("shipping-status")
    assert any(route["id"] == "productShippingStatus" for route in shipping)
