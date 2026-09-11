"""E1.S5 — parameterStrategy shadow + cutover parcial vs OpenAPI binder."""

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


def _product_code_action() -> dict:
    return {
        "actionId": "acme.products.stock",
        "method": "GET",
        "path": "/products/{code}/stock",
        "operationId": "get_product_stock",
        "summary": "Stock",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
        ],
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
    assert shadow["cutover"] is True
    assert shadow["authority"] == "openapi_binder"
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


def test_sale_orders_cutover_uses_openapi_authority():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("sale_orders") is True
    params = ParameterStrategyShadowService.bind_via_openapi(
        _sale_orders_action(),
        "liste pedidos de venda",
    )
    assert isinstance(params, dict)


def test_sale_orders_shadow_reports_cutover_authority():
    invalidate_openapi_tool_routing_cache()
    shadow = ParameterStrategyShadowService.compare(
        strategy="sale_orders",
        legacy_parameters={"page": "1"},
        action=_sale_orders_action(),
        message="liste pedidos de venda",
    )
    assert shadow is not None
    assert shadow["authority"] == "openapi_binder"
    assert shadow["cutover"] is True


def test_product_code_cutover_uses_openapi_authority():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("product_code") is True
    shadow = ParameterStrategyShadowService.compare(
        strategy="product_code",
        legacy_parameters={"code": "10080047"},
        action=_product_code_action(),
        message="estoque 10080047",
        identifier="10080047",
        catalog=_ProductCodeCatalog(),
    )
    assert shadow is not None
    assert shadow["cutover"] is True
    assert shadow["authority"] == "openapi_binder"


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


def test_cutover_off_keeps_strategy_authority(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    from app.domain.services.openapi_tool_routing_content_service import (
        OpenApiToolRoutingContentService,
    )

    original = OpenApiToolRoutingContentService.bool_setting

    def _bool_setting(*path, default=False):
        if path[:2] == ("parameterStrategyShadow", "cutoverEnabled"):
            return False
        return original(*path, default=default)

    monkeypatch.setattr(OpenApiToolRoutingContentService, "bool_setting", _bool_setting)
    assert ParameterStrategyShadowService.uses_openapi_authority("none") is False
    shadow = ParameterStrategyShadowService.compare(
        strategy="none",
        legacy_parameters={},
        action=_generic_action(),
        message="liste itens",
    )
    assert shadow is not None
    assert shadow["authority"] == "strategy"
    assert shadow["cutover"] is False


def test_parameter_strategy_shadow_observability(caplog):
    with caplog.at_level(logging.INFO):
        ParameterStrategyShadowObservabilityService.record(
            {
                "strategy": "sale_orders",
                "authority": "openapi_binder",
                "agree": True,
                "agreeExact": False,
                "agreeCompatible": True,
                "legacyKeyCount": 2,
                "candidateKeyCount": 2,
            }
        )
    assert any("parameter_strategy_shadow" in record.message for record in caplog.records)


class _ProductCodeCatalog:
    def filter_parameters_to_schema(self, action, parameters):
        return parameters

    def build_product_parameters(self, action, code, *, message=None, previous_messages=None):
        return {"code": code}


def test_build_parameters_cutover_none_uses_binder():
    invalidate_openapi_tool_routing_cache()
    from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
        OperationalRouteActionResolverService,
    )

    class _Catalog:
        def filter_parameters_to_schema(self, action, parameters):
            return parameters

    resolver = OperationalRouteActionResolverService(_Catalog())
    route = {"parameters": {"strategy": "none"}}
    params = resolver.build_parameters(
        route,
        _generic_action(),
        message="liste itens genéricos",
        identifier=None,
    )
    assert params == {}


def test_product_code_and_date_branch_openapi_authority():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("product_code") is True
    assert ParameterStrategyShadowService.uses_openapi_authority("date_branch") is True


def test_supplier_part_number_cutover_binds_identifier():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("supplier_part_number") is True
    action = {
        "actionId": "acme.products.by-supplier-pn",
        "method": "GET",
        "path": "/products/by-supplier-part-number",
        "operationId": "search_by_supplier_part_number",
        "parametersSchema": [
            {
                "name": "supplier_part_number",
                "in": "query",
                "required": True,
                "schema": {"type": "string"},
            },
            {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "page_size", "in": "query", "required": False, "schema": {"type": "integer"}},
        ],
        "enabled": True,
    }
    message = "liste produto com part number do fornecedor 008700056"
    params = ParameterStrategyShadowService.bind_via_openapi(
        action,
        message,
        strategy="supplier_part_number",
    )
    assert params is not None
    assert params["supplier_part_number"] == "008700056"
    assert params["page"] == 1


def test_supplier_part_number_missing_returns_none():
    invalidate_openapi_tool_routing_cache()
    action = {
        "actionId": "acme.products.by-supplier-pn",
        "method": "GET",
        "path": "/products/by-supplier-part-number",
        "parametersSchema": [
            {
                "name": "supplier_part_number",
                "in": "query",
                "required": True,
                "schema": {"type": "string"},
            },
        ],
        "enabled": True,
    }
    assert (
        ParameterStrategyShadowService.bind_via_openapi(
            action,
            "olá, tudo bem?",
            strategy="supplier_part_number",
        )
        is None
    )


def test_supplies_stock_cutover_fills_top_limit():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("supplies_stock") is True
    action = {
        "actionId": "acme.supplies.stock-value",
        "method": "GET",
        "path": "/supplies/stock-value",
        "parametersSchema": [
            {"name": "top_limit", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
        ],
        "enabled": True,
    }
    params = ParameterStrategyShadowService.bind_via_openapi(
        action,
        "top estoque de insumos",
        strategy="supplies_stock",
    )
    assert params is not None
    assert "top_limit" in params
    assert int(params["top_limit"]) >= 1


def test_e1s5_all_resolver_strategies_in_cutover():
    invalidate_openapi_tool_routing_cache()
    expected = {
        "schema",
        "none",
        "semantic",
        "sale_orders",
        "supplier_part_number",
        "supplies_stock",
        "exclusive_catalog",
        "lmp",
        "product_search",
        "system_metadata",
        "department_idd",
        "product_code",
        "date_branch",
    }
    assert ParameterStrategyShadowService.cutover_strategies() == expected
    for name in expected:
        assert ParameterStrategyShadowService.uses_openapi_authority(name) is True


def test_product_code_and_date_branch_use_binder_authority():
    invalidate_openapi_tool_routing_cache()
    assert ParameterStrategyShadowService.uses_openapi_authority("product_code") is True
    assert ParameterStrategyShadowService.uses_openapi_authority("date_branch") is True


def test_product_search_cutover_requires_products_search_path():
    invalidate_openapi_tool_routing_cache()
    bad = {
        "actionId": "x",
        "path": "/other/search",
        "operationId": "search_other",
        "parametersSchema": [],
    }
    assert (
        ParameterStrategyShadowService.bind_via_openapi(
            bad,
            "busque produtos cabo",
            strategy="product_search",
        )
        is None
    )
    good = {
        "actionId": "products-search",
        "path": "/products/search",
        "operationId": "search_products",
        "parametersSchema": [
            {"name": "description", "in": "query"},
            {"name": "page_size", "in": "query"},
        ],
    }
    params = ParameterStrategyShadowService.bind_via_openapi(
        good,
        "busque produtos cabo pp",
        strategy="product_search",
    )
    assert params is not None


def test_lmp_cutover_requires_sale_number_when_path_has_placeholder():
    invalidate_openapi_tool_routing_cache()
    action = {
        "actionId": "lmp",
        "path": "/sales/{sale_number}/lmp",
        "parametersSchema": [{"name": "sale_number", "in": "path", "required": True}],
    }
    assert (
        ParameterStrategyShadowService.bind_via_openapi(
            action,
            "mostre o dashboard LMP",
            strategy="lmp",
        )
        is None
    )


def test_build_parameters_ignores_cutover_flag_for_dispatch(monkeypatch):
    """E1.S6: resolver always uses binder for known strategies (flag only affects shadow labels)."""
    invalidate_openapi_tool_routing_cache()
    from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
        OperationalRouteActionResolverService,
    )
    from app.domain.services.openapi_tool_routing_content_service import (
        OpenApiToolRoutingContentService,
    )

    original = OpenApiToolRoutingContentService.bool_setting

    def _bool_setting(*path, default=False):
        if path[:2] == ("parameterStrategyShadow", "cutoverEnabled"):
            return False
        return original(*path, default=default)

    monkeypatch.setattr(OpenApiToolRoutingContentService, "bool_setting", _bool_setting)

    class _Catalog:
        def filter_parameters_to_schema(self, action, parameters):
            return parameters

    resolver = OperationalRouteActionResolverService(_Catalog())
    params = resolver.build_parameters(
        {"parameters": {"strategy": "none"}},
        _generic_action(),
        message="liste itens genéricos",
        identifier=None,
    )
    assert params == {}
    assert ParameterStrategyShadowService.uses_openapi_authority("none") is False


def test_build_parameters_ignores_registry_strategy_uses_schema():
    """E11.S3 — route.parameters.strategy não é authority; schema bind sempre."""
    invalidate_openapi_tool_routing_cache()
    from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
        OperationalRouteActionResolverService,
    )

    class _Catalog:
        def filter_parameters_to_schema(self, action, parameters):
            return parameters

    resolver = OperationalRouteActionResolverService(_Catalog())
    params = resolver.build_parameters(
        {"parameters": {"strategy": "sql"}},
        _generic_action(),
        message="rode sql",
        identifier=None,
    )
    assert isinstance(params, dict)


def test_resolver_attaches_parameter_strategy_shadow_for_none(monkeypatch):
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

    selected = resolver.resolve_route_action(
        route,
        "liste itens genéricos",
        allowed_action_ids=[action["actionId"]],
        candidates=[action],
    )
    assert selected is not None
    shadow = (selected.get("metadata") or {}).get("parameterStrategyShadow")
    assert isinstance(shadow, dict)
    assert shadow["strategy"] == "schema"
    assert shadow["authority"] == "openapi_binder"
    assert selected["arguments"]["parameters"] == {}
