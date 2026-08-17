"""Smoke HTTP — process inspection plan product detail."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_get_process_inspection_plans_product_use_case"
)
def test_process_inspection_plans_product_returns_meta(mock_build) -> None:
    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        get_process_inspection_plans_product_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "product_code": "80010001",
        "include_bom": False,
        "items": [{"product_code": "80010001", "bom_level": 0, "has_inspection": True}],
        "total": 1,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_process_inspection_plans_product_route(
        code="80010001", include_bom=False
    )
    body = _body(response)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_process_inspection_plans_product"
    assert body["meta"]["shape"] == "composite_analysis"
    assert body["meta"]["entity"] == "process_inspection_plans_product"


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_get_process_inspection_plans_product_use_case"
)
def test_process_inspection_plans_product_not_found(mock_build) -> None:
    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        get_process_inspection_plans_product_route,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = None
    mock_build.return_value = mock_use_case

    response = get_process_inspection_plans_product_route(
        code="MISSING", include_bom=False
    )
    assert response.status_code == 404
