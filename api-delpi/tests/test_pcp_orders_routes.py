"""Smoke — /production/pcp-orders."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def pcp_orders_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.pcp_orders_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_summary_items_ranking(pcp_orders_client: TestClient) -> None:
    from app.interface.http.routes.production.pcp_orders_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/pcp-orders"
    assert "/production/pcp-orders/summary" in paths
    assert "/production/pcp-orders/items" in paths
    assert "/production/pcp-orders/ranking" in paths


@patch(
    "app.interface.http.routes.production.pcp_orders_router"
    ".build_get_production_pcp_orders_summary_use_case"
)
def test_summary_returns_envelope(mock_builder, pcp_orders_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "filters": {"delivery_start": "2025-07-01", "delivery_end": "2026-07-01", "branch": "01"},
        "summary": {
            "total_orders": 10,
            "open_orders": 4,
            "delayed_orders": 1,
            "mother_orders": 3,
            "planned_qty_sum": 100.0,
            "produced_qty_sum": 40.0,
            "pending_qty_sum": 60.0,
            "avg_days_late": 2.5,
            "max_days_late": 10,
            "branch": "01",
            "branch_filter_applied": True,
            "consolidated_across_branches": False,
        },
    }
    mock_builder.return_value = use_case

    response = pcp_orders_client.get(
        "/production/pcp-orders/summary",
        params={
            "branch": "01",
            "delivery_start": "2025-07-01",
            "delivery_end": "2026-07-01",
        },
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "get_production_pcp_orders_summary"
    assert payload["meta"]["entity"] == "production_pcp_orders_summary"
    assert payload["meta"]["shape"] == "playbook_report"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["summary"]["total_orders"] == 10


@patch(
    "app.interface.http.routes.production.pcp_orders_router"
    ".build_get_production_pcp_orders_items_use_case"
)
def test_items_returns_paged_list_shape(mock_builder, pcp_orders_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "filters": {"branch": "01"},
        "items": [
            {
                "production_order": "000001",
                "op_key": "01|000001",
                "product_code": "90300005",
                "product_description": "Produto X",
                "description": "Produto X",
                "pending_qty": 5.0,
                "days_late": 2,
                "is_open": True,
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1, "is_complete": True},
    }
    mock_builder.return_value = use_case

    response = pcp_orders_client.get(
        "/production/pcp-orders/items",
        params={"branch": "01", "open_only": True},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_pcp_orders_items"
    assert payload["meta"]["entity"] == "production_pcp_orders_items"
    assert payload["meta"]["shape"] == "paged_list"
    assert payload["data"]["items"][0]["product_description"] == "Produto X"


@patch(
    "app.interface.http.routes.production.pcp_orders_router"
    ".build_get_production_pcp_orders_ranking_use_case"
)
def test_ranking_returns_list_shape(mock_builder, pcp_orders_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "rank_by": "product",
        "metric": "order_qty",
        "limit": 10,
        "items": [{"rank": 1, "product_code": "90300005", "order_qty_sum": 12.0}],
    }
    mock_builder.return_value = use_case

    response = pcp_orders_client.get(
        "/production/pcp-orders/ranking",
        params={"rank_by": "product", "branch": "01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_pcp_orders_ranking"
    assert payload["meta"]["shape"] == "list"
    assert payload["data"]["items"][0]["product_code"] == "90300005"
