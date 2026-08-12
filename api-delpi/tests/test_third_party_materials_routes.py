"""Smoke HTTP — materiais de terceiros."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.third_party_materials_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_expected_paths() -> None:
    from app.interface.http.routes.supplies.third_party_materials_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/third-party-materials"
    assert "/supplies/third-party-materials/shipments" in paths
    assert "/supplies/third-party-materials/shipments/{shipment_recno}" in paths
    assert "/supplies/third-party-materials/summary" in paths
    assert "/supplies/third-party-materials/returns/export" in paths


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.build_list_third_party_materials_shipments_use_case"
)
def test_list_shipments_smoke(mock_builder, _branch, client: TestClient) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 1,
        "is_complete": True,
    }
    mock_builder.return_value = mock_use_case
    response = client.get(
        "/supplies/third-party-materials/shipments",
        params={"branch": "01", "customer_reference": "10018137"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_supplies_third_party_materials_shipments"
    assert body["meta"]["entity"] == "third_party_material_shipment"
    request = mock_use_case.execute.call_args.args[0]
    assert request.customer_reference == "10018137"


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.build_get_third_party_materials_summary_use_case"
)
def test_summary_smoke(mock_builder, _branch, client: TestClient) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "total_shipments": 43,
        "open_shipments": 3,
        "partial_shipments": 1,
        "no_return_shipments": 2,
        "pending_balance": 11419,
    }
    mock_builder.return_value = mock_use_case
    response = client.get(
        "/supplies/third-party-materials/summary",
        params={"branch": "01", "product": "10211413"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["operationId"] == "get_supplies_third_party_materials_summary"
    assert body["data"]["open_shipments"] == 3


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.build_get_third_party_materials_shipment_use_case"
)
def test_shipment_detail_smoke(mock_builder, _branch, client: TestClient) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "shipment_recno": 27062725,
        "status": "partial",
        "returns": [],
    }
    mock_builder.return_value = mock_use_case
    response = client.get(
        "/supplies/third-party-materials/shipments/27062725",
        params={"branch": "01"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["operationId"] == "get_supplies_third_party_materials_shipment"
    assert body["meta"]["entity"] == "third_party_material_shipment"
    assert body["data"]["shipment_recno"] == 27062725


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.build_get_third_party_materials_shipment_use_case"
)
def test_shipment_detail_not_found(mock_builder, _branch, client: TestClient) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = None
    mock_builder.return_value = mock_use_case
    response = client.get(
        "/supplies/third-party-materials/shipments/1",
        params={"branch": "01"},
    )
    assert response.status_code == 404


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
)
def test_branch_forbidden(mock_branch, client: TestClient) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar materiais de terceiros desta filial.",
        status_code=403,
    )
    response = client.get(
        "/supplies/third-party-materials/summary",
        params={"branch": "02"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False


@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.third_party_materials_router.build_export_third_party_materials_returns_use_case"
)
def test_export_csv_smoke(mock_builder, _branch, client: TestClient) -> None:
    from io import BytesIO

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "stream": BytesIO(b"# notice\nshipment_recno\n1\n"),
        "content_type": "text/csv; charset=utf-8",
        "filename": "materiais-terceiros-retornos.csv",
        "exported_count": 1,
    }
    mock_builder.return_value = mock_use_case
    response = client.get(
        "/supplies/third-party-materials/returns/export",
        params={"branch": "01", "product": "10211413", "export_format": "csv"},
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.headers["X-Exported-Count"] == "1"
    assert "materiais-terceiros-retornos.csv" in response.headers["content-disposition"]
    assert response.headers["X-Export-Notice"]
    # StreamingResponse — operationId vive no OpenAPI, não no envelope JSON.
    assert mock_builder.call_count == 1
    assert mock_use_case.execute.call_count == 1
    export_operation_id = "export_supplies_third_party_materials_returns"
    assert export_operation_id.startswith("export_supplies_third_party_materials")
