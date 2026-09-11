"""E11.S5 — registry operationIds sem autoridade de routing."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
    OperationalRouteActionResolverService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    invalidate_openapi_tool_routing_cache,
)


class _Catalog:
    def load_candidates(self, message, *, allowed_action_ids=None, candidates_loader=None):
        _ = message, candidates_loader
        return list(self._actions)

    def stable_sort_by_allowed_action_ids(self, actions, allowed_action_ids):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in actions
            if not allowed or str(action.get("actionId")) in allowed
        ]

    def __init__(self, actions: list[dict]):
        self._actions = actions


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


def _actions() -> list[dict]:
    return [
        {
            "actionId": "acme.products.stock",
            "method": "GET",
            "path": "/products/{code}/stock",
            "operationId": "get_product_stock",
            "summary": "Product stock",
            "parametersSchema": [{"name": "code", "required": True, "in": "path"}],
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.products.structure",
            "method": "GET",
            "path": "/products/{code}/structure",
            "operationId": "get_product_structure",
            "summary": "Product structure",
            "parametersSchema": [{"name": "code", "required": True, "in": "path"}],
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "vendorx.widgets.balance",
            "method": "GET",
            "path": "/widgets/{id}/balance",
            "operationId": "get_widget_balance_renamed",
            "summary": "Unknown vendor widget balance",
            "parametersSchema": [{"name": "id", "required": True, "in": "path"}],
            "sensitivity": "read",
            "enabled": True,
        },
    ]


def test_select_registry_route_id_never_narrows_by_empty_operation_ids(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    catalog = _actions()
    service = ExternalActionSelectionService(_Repo(catalog))
    ids = [row["actionId"] for row in catalog]

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "productStock",
            "domain": "product",
            "intentBinding": "stock",
            "match": {"requiresProductIdentifier": True},
            "route": {"operationIds": [], "method": "GET"},
        },
    )

    def _openapi(message, *, allowed_action_ids, **kwargs):
        assert set(allowed_action_ids) == set(ids)
        return {
            "actionId": "acme.products.stock",
            "arguments": {"actionId": "acme.products.stock", "parameters": {"code": "1"}},
            "metadata": {},
        }

    monkeypatch.setattr(service, "_select_via_openapi_first", _openapi)

    selected = service.select_registry_route_id(
        "productStock",
        "estoque do produto 1",
        allowed_action_ids=ids,
    )
    assert selected is not None
    assert selected["actionId"] == "acme.products.stock"
    shadow = (selected.get("metadata") or {}).get("registrySelectionShadow")
    assert shadow["cutover"] is True


def test_resolver_affinity_picks_sibling_facet_without_operation_ids(monkeypatch):
    resolver = OperationalRouteActionResolverService(_Catalog(_actions()))
    route = {
        "id": "productStructure",
        "domain": "product",
        "intentBinding": "structure",
        "match": {"requiresProductIdentifier": True},
        "route": {"operationIds": [], "method": "GET"},
        "presentation": {"reasonKey": "productStructure"},
    }

    monkeypatch.setattr(
        resolver,
        "resolve_presentation_reason",
        lambda *args, **kwargs: "ok",
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.bind_schema_first",
        lambda action, message, **kwargs: {"code": "10080047"},
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.compare",
        lambda **kwargs: None,
    )

    selected = resolver.resolve_route_action(
        route,
        "estrutura do produto 10080047",
        [row["actionId"] for row in _actions()],
        identifier="10080047",
        candidates=_actions(),
    )
    assert selected is not None
    assert selected["arguments"]["actionId"] == "acme.products.structure"


def test_resolver_unknown_api_without_registry_operation_ids(monkeypatch):
    resolver = OperationalRouteActionResolverService(_Catalog(_actions()))
    route = {
        "id": "vendorxWidgetBalance",
        "domain": "vendorx",
        "intentBinding": "balance",
        "route": {"operationIds": [], "method": "GET"},
        "presentation": {"reasonKey": "widgetBalance"},
    }
    monkeypatch.setattr(
        resolver,
        "resolve_presentation_reason",
        lambda *args, **kwargs: "ok",
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.bind_schema_first",
        lambda action, message, **kwargs: {"id": "w1"},
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.compare",
        lambda **kwargs: None,
    )

    selected = resolver.resolve_route_action(
        route,
        "saldo do widget w1",
        [row["actionId"] for row in _actions()],
        identifier="w1",
        candidates=_actions(),
    )
    assert selected is not None
    assert selected["arguments"]["actionId"] == "vendorx.widgets.balance"


def test_metamorphic_operation_id_rename_still_resolves_by_facet(monkeypatch):
    actions = [
        {
            **row,
            "operationId": row["operationId"] + "_v9",
        }
        for row in _actions()
        if "stock" in row["path"]
    ]
    resolver = OperationalRouteActionResolverService(_Catalog(actions))
    route = {
        "id": "productStock",
        "domain": "product",
        "intentBinding": "stock",
        "match": {"requiresProductIdentifier": True},
        "route": {
            "operationIds": ["totally_unknown_legacy_id"],
            "method": "GET",
        },
        "presentation": {"reasonKey": "productStock"},
    }
    monkeypatch.setattr(
        resolver,
        "resolve_presentation_reason",
        lambda *args, **kwargs: "ok",
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.bind_schema_first",
        lambda action, message, **kwargs: {"code": "1"},
    )
    monkeypatch.setattr(
        "app.domain.services.parameter_strategy_shadow_service."
        "ParameterStrategyShadowService.compare",
        lambda **kwargs: None,
    )

    selected = resolver.resolve_route_action(
        route,
        "estoque 1",
        [row["actionId"] for row in actions],
        identifier="1",
        candidates=actions,
    )
    assert selected is not None
    assert selected["arguments"]["actionId"] == "acme.products.stock"
