"""J-R7 — zero path semantic affinity no resolver."""

from __future__ import annotations

from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
    OperationalRouteActionResolverService,
)


def test_j_r7_positive_structure_selected_by_facet_not_path():
    """Sibling stock vs structure: facet/summary, mesmo sem /structure no path HTTP."""
    actions = [
        {
            "actionId": "acme.inventory.onhand",
            "method": "GET",
            "path": "/inventory/{sku}/on-hand",  # sem /products/ nem /structure
            "operationId": "get_on_hand",
            "summary": "Product stock on hand",
            "parametersSchema": [{"name": "code", "required": True, "in": "path"}],
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.bom.tree",
            "method": "GET",
            "path": "/bom/{sku}/tree",  # sem /products/
            "operationId": "get_bom_tree",
            "summary": "Product structure bill of materials",
            "parametersSchema": [{"name": "code", "required": True, "in": "path"}],
            "sensitivity": "read",
            "enabled": True,
        },
    ]
    resolver = OperationalRouteActionResolverService(catalog=None)
    route = {
        "id": "productStructure",
        "domain": "product",
        "intentBinding": "structure",
        "match": {"requiresProductIdentifier": True},
        "route": {"operationIds": [], "method": "GET"},
    }
    assert resolver._action_fits_route_affinity(route, actions[1], path=actions[1]["path"])
    assert not resolver._action_fits_route_affinity(route, actions[0], path=actions[0]["path"])


def test_j_r7_sibling_search_by_schema_not_products_path():
    resolver = OperationalRouteActionResolverService(catalog=None)
    route = {
        "id": "productSearchByDescription",
        "domain": "domainProductSearch",
        "route": {"method": "GET"},
    }
    ok = {
        "path": "/catalog/items/lookup",
        "summary": "Search catalog items",
        "parametersSchema": [{"name": "description", "in": "query"}],
    }
    bad = {
        "path": "/products/{code}/stock",
        "summary": "Product stock",
        "parametersSchema": [{"name": "code", "in": "path"}],
    }
    assert resolver._action_fits_route_affinity(route, ok, path=ok["path"])
    assert not resolver._action_fits_route_affinity(route, bad, path=bad["path"])


def test_j_r7_negative_no_hardcoded_products_search_path_rule():
    """Regressão A11-07: path /products/.../search sozinho não prova affinity."""
    import inspect

    source = inspect.getsource(OperationalRouteActionResolverService._action_fits_route_affinity)
    assert '"/products/" in' not in source
    assert '"search" in path' not in source
    assert "_facet_hits_path" not in source
