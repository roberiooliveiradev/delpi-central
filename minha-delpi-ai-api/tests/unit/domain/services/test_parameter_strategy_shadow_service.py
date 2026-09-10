"""E1.S5 — parameterStrategy shadow vs OpenAPI binder (sem cutover)."""

from __future__ import annotations

import logging

from app.domain.services.openapi_tool_routing_content_service import (
    invalidate_openapi_tool_routing_cache,
)
from app.domain.services.parameter_strategy_shadow_service import (
    ParameterStrategyShadowObservabilityService,
    ParameterStrategyShadowService,
)


def _sale_orders_action() -> dict:
    return {
        "actionId": "acme.sale-orders.list",
        "method": "GET",
        "path": "/sale-orders",
        "operationId": "list_sale_orders",
        "summary": "List sale orders",
        "parametersSchema": [
            {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "page_size", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "start_date", "in": "query", "required": False, "schema": {"type": "string"}},
            {"name": "end_date", "in": "query", "required": False, "schema": {"type": "string"}},
        ],
        "sensitivity": "read",
        "enabled": True,
    }


def _generic_action() -> dict:
    return {
        "actionId": "acme.generic.read",
        "method": "GET",
        "path": "/generic/items",
        "operationId": "list_generic_items",
        "summary": "Generic list",
        "parametersSchema": [],
        "sensitivity": "read",
        "enabled": True,
    }


def test_none_strategy_shadow_agrees_on_empty_params():
    invalidate_openapi_tool_routing_cache()
    shadow = ParameterStrategyShadowService.compare(
        strategy="none",
        legacy_parameters={},
        action=_generic_action(),
        message="liste itens genéricos",
    )
    assert shadow is not None
    assert shadow["strategy"] == "none"
    assert shadow["agreeExact"] is True
    assert shadow["agree"] is True


def test_semantic_strategy_shadow_agrees_on_empty_params():
    invalidate_openapi_tool_routing_cache()
    shadow = ParameterStrategyShadowService.compare(
        strategy="semantic",
        legacy_parameters={},
        action=_generic_action(),
        message="mostre documentos comerciais",
    )
    assert shadow is not None
    assert shadow["agree"] is True


def test_sale_orders_compatible_when_legacy_subset():
    invalidate_openapi_tool_routing_cache()
    legacy = {"page": "1", "page_size": "50"}
    shadow = ParameterStrategyShadowService.compare(
        strategy="sale_orders",
        legacy_parameters=legacy,
        action=_sale_orders_action(),
        message="liste pedidos de venda",
    )
    assert shadow is not None
    assert shadow["agreeCompatible"] is True or shadow["agreeExact"] is True
    # Authority unchanged by design — this only observes.
    assert "legacyParameters" in shadow


def test_non_shadowable_strategy_returns_none():
    invalidate_openapi_tool_routing_cache()
    assert (
        ParameterStrategyShadowService.compare(
            strategy="product_code",
            legacy_parameters={"code": "10080047"},
            action=_sale_orders_action(),
            message="estoque 10080047",
        )
        is None
    )


def test_flag_off_skips_shadow(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    from app.domain.services.openapi_tool_routing_content_service import (
        OpenApiToolRoutingContentService,
    )

    original = OpenApiToolRoutingContentService.bool_setting

    def _bool_setting(*path, default=False):
        if path[:2] == ("parameterStrategyShadow", "enabled"):
            return False
        return original(*path, default=default)

    monkeypatch.setattr(OpenApiToolRoutingContentService, "bool_setting", _bool_setting)
    assert (
        ParameterStrategyShadowService.compare(
            strategy="none",
            legacy_parameters={},
            action=_generic_action(),
            message="x",
        )
        is None
    )


def test_parameter_strategy_shadow_observability(caplog):
    with caplog.at_level(logging.INFO):
        ParameterStrategyShadowObservabilityService.record(
            {
                "strategy": "sale_orders",
                "agree": True,
                "agreeExact": False,
                "agreeCompatible": True,
                "legacyKeyCount": 2,
                "candidateKeyCount": 2,
            }
        )
    assert any("parameter_strategy_shadow" in record.message for record in caplog.records)


def test_resolver_attaches_parameter_strategy_shadow_for_none(monkeypatch):
    """Wiring: resolve_route_action anexa metadata quando strategy=none."""
    invalidate_openapi_tool_routing_cache()
    from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
        OperationalRouteActionResolverService,
    )

    class _Catalog:
        def find_allowed_actions_by_markers(self, **kwargs):
            return []

        def load_candidates(self, *args, **kwargs):
            return []

        def filter_parameters_to_schema(self, action, parameters):
            return parameters

        def stable_sort_by_allowed_action_ids(self, candidates, allowed_action_ids):
            return list(candidates)

    resolver = OperationalRouteActionResolverService(_Catalog())
    action = _generic_action()
    route = {
        "parameters": {"strategy": "none"},
        "route": {
            "pathMarkers": ["/generic"],
            "method": "GET",
        },
        "presentation": {"reasonFormatKey": ""},
        "onMultipleMatches": "",
    }

    monkeypatch.setattr(
        resolver,
        "_action_fits_route_affinity",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        resolver,
        "build_parameters",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        resolver,
        "resolve_presentation_reason",
        lambda *args, **kwargs: "generic.list",
    )

    # Inject candidate via candidates= to skip marker catalog load
    selected = resolver.resolve_route_action(
        route,
        "liste itens genéricos",
        allowed_action_ids=[action["actionId"]],
        candidates=[action],
    )
    assert selected is not None
    shadow = (selected.get("metadata") or {}).get("parameterStrategyShadow")
    assert isinstance(shadow, dict)
    assert shadow["strategy"] == "none"
    assert selected["arguments"]["parameters"] == {}
