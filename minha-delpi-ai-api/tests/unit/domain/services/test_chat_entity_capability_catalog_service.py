from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)


def test_available_excludes_executed_route():
    remaining = ChatEntityCapabilityCatalogService.available(
        domain="product",
        allowed_action_ids=["get_product_stock", "get_product_structure"],
        executed_route_ids={"productStock"},
    )

    route_ids = {item["routeId"] for item in remaining}

    assert "productStock" not in route_ids
    assert "productStructure" in route_ids or "productSummary" in route_ids


def test_limits_are_positive():
    assert ChatEntityCapabilityCatalogService.max_extra_routes_per_turn() > 0
    assert ChatEntityCapabilityCatalogService.max_fan_out_keys() > 0
