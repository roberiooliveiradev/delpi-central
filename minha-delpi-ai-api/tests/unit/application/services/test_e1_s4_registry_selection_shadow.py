"""E1.S4 — registry marker selection vs retrieval shadow (sem mudar a action escolhida)."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    invalidate_openapi_tool_routing_cache,
)


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def _stock_catalog() -> list[dict]:
    return [
        {
            "actionId": "acme.products.stock",
            "method": "GET",
            "path": "/products/{code}/stock",
            "operationId": "get_product_stock",
            "summary": "Product stock balance by code",
            "description": "Saldo de estoque disponível por código de produto.",
            "whenToUse": "estoque, saldo disponível",
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.products.search",
            "method": "GET",
            "path": "/products/search",
            "operationId": "search_products",
            "summary": "Search products by description",
            "description": "Busca produtos pela descrição sem código.",
            "whenToUse": "liste produtos, busque pela descrição",
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.shipments.tracking",
            "method": "GET",
            "path": "/shipments/{id}/tracking",
            "operationId": "get_shipment_tracking",
            "summary": "Shipment tracking",
            "description": "Rastreio de remessa.",
            "whenToUse": "rastreio de remessa",
            "sensitivity": "read",
            "enabled": True,
        },
    ]


def test_registry_selection_shadow_agrees_when_prose_matches(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    catalog = _stock_catalog()
    service = ExternalActionSelectionService(_Repo(catalog))

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "product.stock",
            "route": {"pathMarkers": ["/stock"], "operationIdMarkers": ["stock"]},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda *args, **kwargs: {
            "name": "execute_external_action",
            "actionId": "acme.products.stock",
            "arguments": {"actionId": "acme.products.stock", "parameters": {}},
            "metadata": {},
            "selectionMode": "openapi_first",
        },
    )

    selected = service.select_registry_route_id(
        "product.stock",
        "qual o estoque do produto 10080047",
        allowed_action_ids=[row["actionId"] for row in catalog],
    )
    assert selected is not None
    shadow = (selected.get("metadata") or {}).get("registrySelectionShadow")
    assert isinstance(shadow, dict)
    assert shadow["legacyActionId"] == "acme.products.stock"
    assert shadow["agree"] is True
    assert "acme.products.stock" in shadow["candidateTopIds"]


def test_registry_selection_shadow_diverges_when_markers_force_wrong_family(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    catalog = _stock_catalog()
    service = ExternalActionSelectionService(_Repo(catalog))

    # Markers force stock, but message is about tracking — retrieval should prefer tracking.
    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "product.stock",
            "route": {"pathMarkers": ["/stock"], "operationIdMarkers": ["stock"]},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda *args, **kwargs: {
            "name": "execute_external_action",
            "actionId": "acme.products.stock",
            "arguments": {"actionId": "acme.products.stock", "parameters": {}},
            "metadata": {},
            "selectionMode": "openapi_first",
        },
    )

    selected = service.select_registry_route_id(
        "product.stock",
        "onde está a remessa 45871",
        allowed_action_ids=[row["actionId"] for row in catalog],
    )
    assert selected is not None
    # Authority still stock (legacy) — shadow only observes.
    assert selected["actionId"] == "acme.products.stock"
    shadow = (selected.get("metadata") or {}).get("registrySelectionShadow")
    assert shadow["agree"] is False
    assert shadow["candidateTopIds"][0] == "acme.shipments.tracking"


def test_registry_selection_shadow_can_be_disabled(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    catalog = _stock_catalog()
    service = ExternalActionSelectionService(_Repo(catalog))

    from app.domain.services.openapi_tool_routing_content_service import (
        OpenApiToolRoutingContentService,
    )

    original = OpenApiToolRoutingContentService.bool_setting

    def _bool_setting(*path, default=False):
        if path[:2] == ("registrySelectionShadow", "enabled"):
            return False
        return original(*path, default=default)

    monkeypatch.setattr(OpenApiToolRoutingContentService, "bool_setting", _bool_setting)
    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "product.stock",
            "route": {"pathMarkers": ["/stock"]},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda *args, **kwargs: {
            "actionId": "acme.products.stock",
            "metadata": {},
        },
    )

    selected = service.select_registry_route_id(
        "product.stock",
        "estoque do produto",
        allowed_action_ids=[row["actionId"] for row in catalog],
    )
    assert selected is not None
    assert "registrySelectionShadow" not in (selected.get("metadata") or {})
