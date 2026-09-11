"""E11.S4 — continuity facets from structured route metadata (not path-tail)."""

from __future__ import annotations

from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
    invalidate_operational_route_registry_cache,
)
from app.domain.services.route_segment_inference_service import (
    RouteSegmentInferenceService,
    invalidate_route_segment_inference_cache,
)


def setup_function() -> None:
    invalidate_operational_route_registry_cache()
    invalidate_route_segment_inference_cache()


def test_path_tail_stubs_are_empty() -> None:
    assert RouteSegmentInferenceService.continuity_keys_from_path(
        "/products/{code}/sales/open-orders"
    ) == frozenset()
    assert RouteSegmentInferenceService.path_for_operation_id("get_product_stock") is None


def test_routes_by_segment_from_route_id_and_facets() -> None:
    for route in OperationalRouteRegistryService.routes():
        assert "routeSegment" not in route

    guide = OperationalRouteRegistryService.routes_by_segment("guide")
    assert guide
    assert guide[0]["id"] == "productGuide"

    open_orders = OperationalRouteRegistryService.routes_by_segment("open-orders")
    assert any(route["id"] == "productOpenOrders" for route in open_orders)

    inbound = OperationalRouteRegistryService.routes_by_segment("inbound-invoice")
    assert any(route["id"] == "productInvoicesInbound" for route in inbound)


def test_refinement_intent_map_from_intent_binding() -> None:
    mapping = OperationalRouteRegistryService.refinement_intent_by_route_segment()
    assert mapping["stock"] == "stock"
    assert mapping["structure"] == "structure"
    assert mapping["parents"] == "parents"


def test_shipping_status_from_route_id_facet() -> None:
    shipping = OperationalRouteRegistryService.routes_by_segment("shipping-status")
    assert any(route["id"] == "productShippingStatus" for route in shipping)


def test_metamorphic_operation_id_ignored_for_continuity() -> None:
    route = {
        "id": "productStock",
        "domain": "product",
        "intentBinding": "stock",
        "route": {"operationIds": ["totally_renamed_op"], "method": "GET"},
        "match": {"requiresProductIdentifier": True},
    }
    keys = RouteSegmentInferenceService.continuity_keys_for_route(route)
    assert "stock" in keys
    assert RouteSegmentInferenceService.has_product_continuity_segment(route) is True
