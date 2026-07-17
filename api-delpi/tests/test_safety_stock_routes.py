from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockItemsRequest,
    SafetyStockQueryRequest,
)
from app.application.services.response_meta_builder import DATA_VERSION
from app.core.exceptions import DatabaseConnectionError


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def safety_stock_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.safety_stock_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints(safety_stock_client: TestClient) -> None:
    from app.interface.http.routes.supplies.safety_stock_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/safety-stock"
    assert "/supplies/safety-stock/filters" in paths
    assert "/supplies/safety-stock/summary" in paths
    assert "/supplies/safety-stock/items" in paths
    assert "/supplies/safety-stock/items/{code}/details" in paths
    assert "/supplies/safety-stock/items/{code}/suppliers" in paths
    assert (
        "/supplies/safety-stock/items/{code}/suppliers/"
        "{supplier_code}/purchase-price-history"
    ) in paths


def test_summary_requires_branch(safety_stock_client: TestClient) -> None:
    response = safety_stock_client.get("/supplies/safety-stock/summary")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_summary_use_case"
)
def test_summary_returns_envelope(mock_builder, _mock_branch, safety_stock_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "total_materials": 10,
        "with_safety_stock": 5,
        "without_safety_stock": 5,
        "below_safety_stock": 2,
        "at_safety_stock": 1,
        "above_safety_stock": 2,
        "with_primary_stock": 8,
        "without_primary_stock": 2,
        "with_work_in_process_stock": 3,
        "deficit_by_unit": [],
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/summary",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_supplies_safety_stock_summary"
    assert body["meta"]["entity"] == "supplies_safety_stock_summary"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_item_details_use_case"
)
def test_item_details_returns_composite_meta(
    mock_builder, _mock_branch, safety_stock_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "product": {"product_code": "10010005", "branch": "01"},
        "stock": {"deficit_quantity": 10},
        "purchase_coverage": {"status": "none"},
        "open_purchase_orders": {"items": [], "total": 0},
        "open_commitments": {"items": [{"production_order": "OP1"}], "total": 1},
        "stock_projection": {
            "items": [{"origin": "initial_balance"}],
            "total": 1,
            "summary": {"status": "sufficient"},
        },
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/10010005/details",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_supplies_safety_stock_item_details"
    assert body["meta"]["entity"] == "supplies_safety_stock_detail"
    assert body["meta"]["shape"] == "composite_analysis"
    section_keys = {section["key"] for section in body["meta"]["sections"]}
    assert section_keys == {
        "open_purchase_orders",
        "open_commitments",
        "stock_projection",
    }
    assert body["meta"]["sections"][1]["itemCount"] == 1


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_item_details_use_case"
)
def test_item_details_returns_404_when_missing(
    mock_builder, _mock_branch, safety_stock_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = None
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/MISSING/details",
        params={"branch": "01"},
    )
    assert response.status_code == 404


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_item_suppliers_use_case"
)
def test_item_suppliers_returns_list_meta(
    mock_builder, _mock_branch, safety_stock_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "supplier_code": "F001",
                "supplier_store": "01",
                "trade_name": "ACME",
                "has_last_purchase": True,
                "last_unit_price": 12.5,
            }
        ],
        "total": 1,
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/10010005/suppliers",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_supplies_safety_stock_item_suppliers"
    assert body["meta"]["entity"] == "supplies_safety_stock_supplier"
    assert body["meta"]["shape"] == "list"
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["last_unit_price"] == 12.5


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
)
def test_item_suppliers_denies_branch_without_permission(
    mock_branch, safety_stock_client: TestClient
) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar estoque de segurança desta filial.",
        status_code=403,
    )

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/10010005/suppliers",
        params={"branch": "02"},
    )
    assert response.status_code == 403


def test_route_contract_registry_contains_suppliers_operation() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    contract = ROUTE_CONTRACTS["get_supplies_safety_stock_item_suppliers"]
    assert contract.entity == "supplies_safety_stock_supplier"
    assert contract.shape == "list"


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_supplier_price_history_use_case"
)
def test_supplier_price_history_returns_playbook_meta(
    mock_builder, _mock_branch, safety_stock_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "product_code": "10010005",
        "branch": "01",
        "supplier_code": "F001",
        "supplier_store": "01",
        "date_start": "20250717",
        "date_end_exclusive": "20260718",
        "items": [{"unit_price": 10.0, "purchase_date": "2026-01-15"}],
        "total": 1,
        "summary": {
            "total_purchases": 1,
            "min_unit_price": 10.0,
            "max_unit_price": 10.0,
            "first_unit_price": 10.0,
            "last_unit_price": 10.0,
            "variation_percent": None,
        },
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/10010005/suppliers/F001/purchase-price-history",
        params={"branch": "01", "supplierStore": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert (
        body["meta"]["operationId"]
        == "get_supplies_safety_stock_supplier_purchase_price_history"
    )
    assert body["meta"]["entity"] == "supplies_safety_stock_supplier_price_history"
    assert body["meta"]["shape"] == "playbook_report"
    assert body["data"]["total"] == 1
    request = use_case.execute.call_args.args[0]
    assert request.supplier_code == "F001"
    assert request.supplier_store == "01"


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
)
def test_supplier_price_history_denies_branch_without_permission(
    mock_branch, safety_stock_client: TestClient
) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar estoque de segurança desta filial.",
        status_code=403,
    )

    response = safety_stock_client.get(
        "/supplies/safety-stock/items/10010005/suppliers/F001/purchase-price-history",
        params={"branch": "02", "supplierStore": "01"},
    )
    assert response.status_code == 403


def test_route_contract_registry_contains_supplier_price_history_operation() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    contract = ROUTE_CONTRACTS[
        "get_supplies_safety_stock_supplier_purchase_price_history"
    ]
    assert contract.entity == "supplies_safety_stock_supplier_price_history"
    assert contract.shape == "playbook_report"


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_items_use_case"
)
def test_items_returns_paged_meta(mock_builder, _mock_branch, safety_stock_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
        "sort_by": "product_code",
        "sort_direction": "asc",
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items",
        params={"branch": "01", "page": 1, "pageSize": 50},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_supplies_safety_stock_items"
    assert body["meta"]["entity"] == "supplies_safety_stock_item"
    assert body["meta"]["shape"] == "paged_list"


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
)
def test_summary_denies_branch_without_permission(mock_branch, safety_stock_client: TestClient) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar estoque de segurança desta filial.",
        status_code=403,
    )

    response = safety_stock_client.get(
        "/supplies/safety-stock/summary",
        params={"branch": "02"},
    )
    body = _body(response)

    assert response.status_code == 403
    assert body["success"] is False


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_summary_use_case"
)
def test_summary_handles_database_unavailable(
    mock_builder,
    _mock_branch,
    safety_stock_client: TestClient,
) -> None:
    use_case = MagicMock()
    use_case.execute.side_effect = DatabaseConnectionError("falha")
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/summary",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 503
    assert body["success"] is False


def test_items_request_rejects_invalid_sort_field() -> None:
    with pytest.raises(ValueError, match="ordenação"):
        SafetyStockItemsRequest(branch="01", sort_by="sql_injection")


def test_items_request_rejects_oversized_page() -> None:
    with pytest.raises(ValueError, match="page_size"):
        SafetyStockItemsRequest(branch="01", page_size=500)


def test_query_request_requires_branch() -> None:
    with pytest.raises(ValueError, match="branch"):
        SafetyStockQueryRequest(branch="")


def test_query_request_rejects_invalid_status() -> None:
    with pytest.raises(ValueError, match="Status"):
        SafetyStockQueryRequest(branch="01", status="invalid")


@patch(
    "app.interface.http.routes.supplies.safety_stock_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.safety_stock_router.build_get_safety_stock_items_use_case"
)
def test_items_passes_filters_to_use_case(
    mock_builder,
    _mock_branch,
    safety_stock_client: TestClient,
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [{"product_code": "MP001", "status": "below_safety_stock"}],
        "page": 2,
        "page_size": 25,
        "total": 1,
        "total_pages": 1,
        "sort_by": "primary_stock",
        "sort_direction": "desc",
    }
    mock_builder.return_value = use_case

    response = safety_stock_client.get(
        "/supplies/safety-stock/items",
        params={
            "branch": "01",
            "page": 2,
            "pageSize": 25,
            "search": "MP001",
            "status": "below_safety_stock",
            "sortBy": "primary_stock",
            "sortDirection": "desc",
            "includeBlocked": True,
        },
    )

    assert response.status_code == 200
    request = use_case.execute.call_args.args[0]
    assert request.branch == "01"
    assert request.search == "MP001"
    assert request.status == "below_safety_stock"
    assert request.include_blocked is True
    assert request.sort_by == "primary_stock"
    assert request.sort_direction == "desc"
