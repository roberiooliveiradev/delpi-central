"""E11.S3 — path/operationId no longer select parameter strategy."""

from __future__ import annotations

from app.domain.services.parameter_strategy_inference_service import (
    ParameterStrategyInferenceService,
)
from app.domain.services.parameter_strategy_shadow_service import (
    ParameterStrategyShadowService,
)


def test_infer_always_schema_regardless_of_path():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/products/{code}/stock",
            operation_id="get_product_stock",
        )
        == "schema"
    )


def test_infer_sibling_production_path_also_schema():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/production/orders/open",
            operation_id="get_production_orders_open",
        )
        == "schema"
    )


def test_infer_negative_unknown_path_schema():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/cultura-delpi/content",
        )
        == "schema"
    )


def test_route_declared_strategy_ignored_for_authority_label():
    got = ParameterStrategyInferenceService.infer_from_action(
        {"path": "/products/{code}/stock", "operationId": "get_product_stock"},
        route={"parameters": {"strategy": "date_branch"}},
    )
    assert got == "schema"


def test_bind_schema_first_product_code_positive():
    action = {
        "actionId": "api.stock",
        "path": "/products/{code}/stock",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
            {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
        ],
    }
    params = ParameterStrategyShadowService.bind_schema_first(
        action,
        "estoque do produto 10080001",
        identifier="10080001",
    )
    assert isinstance(params, dict)
    assert str(params.get("code") or "") == "10080001"


def test_bind_schema_first_required_code_missing_negative():
    action = {
        "actionId": "api.stock",
        "path": "/products/{code}/stock",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
        ],
    }
    params = ParameterStrategyShadowService.bind_schema_first(
        action,
        "como vai o tempo hoje",
    )
    assert params is None


def test_bind_schema_first_metamorphic_path_rename():
    schema = [
        {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
    ]
    before = ParameterStrategyShadowService.bind_schema_first(
        {"path": "/products/{code}/stock", "parametersSchema": schema},
        "produto 10080001",
        identifier="10080001",
    )
    after = ParameterStrategyShadowService.bind_schema_first(
        {"path": "/catalog/items/{code}/inventory", "parametersSchema": schema},
        "produto 10080001",
        identifier="10080001",
    )
    assert before is not None and after is not None
    assert before.get("code") == after.get("code") == "10080001"
