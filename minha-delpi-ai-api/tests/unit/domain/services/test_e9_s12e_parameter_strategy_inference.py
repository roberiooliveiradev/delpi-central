"""E9.S12.E — parameter strategy inference (OpenAPI path/operationId)."""

from __future__ import annotations

from app.domain.services.parameter_strategy_inference_service import (
    ParameterStrategyInferenceService,
)


def test_e9_s12e_product_code_from_products_path():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/products/{code}/stock",
            operation_id="get_product_stock",
        )
        == "product_code"
    )


def test_e9_s12e_sibling_date_branch_production():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/production/orders/open",
            operation_id="get_production_orders_open",
        )
        == "date_branch"
    )


def test_e9_s12e_negative_generic_content_is_none():
    assert (
        ParameterStrategyInferenceService.infer_from_path(
            "/cultura-delpi/content",
        )
        == "none"
    )


def test_e9_s12e_route_declared_strategy_still_overrides():
    got = ParameterStrategyInferenceService.infer_from_action(
        {"path": "/products/{code}/stock", "operationId": "get_product_stock"},
        route={"parameters": {"strategy": "date_branch"}},
    )
    assert got == "date_branch"
