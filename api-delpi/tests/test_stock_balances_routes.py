"""Smoke e unitários — /supplies/stock-balances."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.infrastructure.persistence.totvs.supplies_repositories import (
    stock_balances_sql as sql,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def stock_balances_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.stock_balances_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_summary_and_items(stock_balances_client: TestClient) -> None:
    from app.interface.http.routes.supplies.stock_balances_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/stock-balances"
    assert "/supplies/stock-balances/summary" in paths
    assert "/supplies/stock-balances/items" in paths


def test_sql_valuation_uses_qatu_times_cm1_same_local() -> None:
    assert "B2_QATU" in sql.STOCK_VALUE_EXPR
    assert "B2_CM1" in sql.STOCK_VALUE_EXPR
    assert "AVG(" not in sql.STOCK_VALUE_EXPR.upper()
    where, params = sql.build_where_clause(
        branch="01",
        warehouse="50",
        only_positive=True,
    )
    assert "B2_FILIAL" in where
    assert "B2_LOCAL" in where
    assert "B2_QATU > 0" in where
    assert params == ["01", "50"]
    summary = sql.format_summary_sql(where)
    assert "AVG(" not in summary.upper()
    assert sql.STOCK_VALUE_EXPR in summary
    items = sql.format_items_sql(where, order_by=sql.resolve_order_by(None))
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in items
    assert "SB1010" in items


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_summary_returns_envelope(mock_builder, stock_balances_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "branch": "01",
            "warehouse": "50",
            "product_count": 4,
            "total_quantity": 100.0,
            "total_stock_value": 52481.83,
            "total_stock_value_vatu1": 52481.83,
            "warehouse_count": 1,
            "valuation": "qatu_times_cm1_same_local",
        },
        "by_warehouse": [
            {
                "branch": "01",
                "warehouse": "50",
                "warehouse_label": "WIP / processo",
                "product_count": 4,
                "total_quantity": 100.0,
                "total_stock_value": 52481.83,
                "total_stock_value_vatu1": 52481.83,
            }
        ],
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params={"branch": "01", "warehouse": "50"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_supplies_stock_balances_summary"
    assert body["meta"]["entity"] == "supplies_stock_balances_summary"
    assert body["meta"]["shape"] == "playbook_report"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["summary"]["product_count"] == 4
    use_case.execute.assert_called_once()


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_items_use_case"
)
def test_items_returns_envelope(mock_builder, stock_balances_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "product_code": "10070821",
                "description": "CABO PP",
                "branch": "01",
                "warehouse": "50",
                "quantity": 10.0,
                "unit_cost": 1.5,
                "stock_value": 15.0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "sort": "stock_value_desc",
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/items",
        params={"branch": "01", "warehouse": "50", "page": 1},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_supplies_stock_balances_items"
    assert body["meta"]["entity"] == "supplies_stock_balances_item"
    assert body["meta"]["shape"] == "paged_list"
    assert body["data"]["items"][0]["product_code"] == "10070821"


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_location_alias_maps_to_warehouse(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"summary": {}, "by_warehouse": []}
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params={"location": "25"},
    )
    assert response.status_code == 200
    req = use_case.execute.call_args.args[0]
    assert req.warehouse == "25"
