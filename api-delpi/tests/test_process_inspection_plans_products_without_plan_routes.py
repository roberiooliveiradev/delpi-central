"""Smoke HTTP — products without process inspection plan."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_list_process_inspection_plans_products_without_plan_use_case"
)
def test_process_inspection_plans_products_without_plan_returns_meta(
    mock_build, _mock_branch
) -> None:
    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        get_process_inspection_plans_products_without_plan_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [
            {
                "product_code": "80012849",
                "product_description": "Item",
                "open_orders_count": 2,
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_process_inspection_plans_products_without_plan_route(
        branch="01", page=1, page_size=50
    )
    body = _body(response)
    assert body["success"] is True
    assert (
        body["meta"]["operationId"]
        == "get_process_inspection_plans_products_without_plan"
    )
    assert body["meta"]["shape"] == "paged_list"
    assert body["meta"]["entity"] == "process_inspection_plans_products_without_plan"
