"""Smoke HTTP — products with process inspection plan."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.process_inspection_plans.process_inspection_plans_router.build_list_process_inspection_plans_products_use_case"
)
def test_process_inspection_plans_products_returns_meta(mock_build) -> None:
    from app.interface.http.routes.process_inspection_plans.process_inspection_plans_router import (
        get_process_inspection_plans_products_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [
            {
                "product_code": "80010001",
                "product_description": "Item",
                "revision": "001",
                "description": "Plan",
                "inspection_type": "P",
                "created_at": "20240101",
                "start_date": "20240101",
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

    response = get_process_inspection_plans_products_route(page=1, page_size=50)
    body = _body(response)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_process_inspection_plans_products"
    assert body["meta"]["shape"] == "paged_list"
    assert body["meta"]["entity"] == "process_inspection_plans_products"
