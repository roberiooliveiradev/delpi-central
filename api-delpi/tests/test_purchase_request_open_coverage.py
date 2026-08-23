from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.use_cases.supplies.get_purchase_requests_open_coverage_use_case import (
    GetPurchaseRequestsOpenCoverageUseCase,
)
from app.domain.services.supplies.purchase_request_open_coverage_service import (
    build_purchase_request_open_coverage,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    available_stock_for_open_purchase_request_products_sql,
    open_purchase_requests_sql,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


def test_open_purchase_requests_sql_omits_product_when_unscoped() -> None:
    sql, params = open_purchase_requests_sql(
        branch="01",
        product_param=None,
        product_type=PRODUCT_TYPE_RAW_MATERIAL,
    )
    assert "SC1010" in sql
    assert "C1_QUANT > SC1.C1_QUJE" in sql
    assert "C1_PRODUTO) =" not in sql
    assert f"B1_TIPO) = '{PRODUCT_TYPE_RAW_MATERIAL}'" in sql
    assert params == ["01"]


def test_open_purchase_requests_sql_item_details_does_not_force_mp() -> None:
    sql, _params = open_purchase_requests_sql(branch="01")
    assert "C1_PRODUTO) =" in sql
    assert "B1_TIPO" not in sql


def test_open_purchase_requests_sql_rejects_unknown_product_type() -> None:
    with pytest.raises(ValueError, match="unsupported product_type"):
        open_purchase_requests_sql(branch="01", product_param=None, product_type="XX")


def test_available_stock_sql_scopes_to_open_sc1_mp_products() -> None:
    sql, params = available_stock_for_open_purchase_request_products_sql(branch="02")
    assert "SC1010" in sql
    assert "SB2010" in sql
    assert "SBZ010" in sql
    assert "safety_stock" in sql
    assert "BZ_ESTSEG" in sql
    assert "B2_LOCAL" in sql
    assert "'01'" in sql
    assert "'98'" in sql
    assert "'99'" in sql
    assert "available_stock" in sql
    assert f"B1_TIPO) = '{PRODUCT_TYPE_RAW_MATERIAL}'" in sql
    assert params == ["02", "02", "02", "02"]


def test_coverage_adds_projected_balance_from_stock_orders_and_commitments() -> None:
    payload = build_purchase_request_open_coverage(
        requests=[
            {
                "branch": "01",
                "request_number": "SC001",
                "request_item": "01",
                "product_code": "10020113",
                "product_description": "Cobre",
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 50.0,
                "issue_date": "2026-08-01",
                "required_date": "2026-08-20",
                "supplier_code": "F01",
                "supplier_name": "Fornecedor",
            }
        ],
        stocks=[
            {
                "product_code": "10020113",
                "unit": "KG",
                "secondary_unit": "",
                "conversion_factor": None,
                "conversion_type": "",
                "available_stock": 80.0,
                "safety_stock": 20.0,
            }
        ],
        orders=[
            {
                "product_code": "10020113",
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 20.0,
            }
        ],
        commitments=[
            {
                "product_code": "10020113",
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 10.0,
                "commitment_date": "20260822",
            }
        ],
    )

    items = payload["items"]
    assert len(items) == 1
    coverage = items[0]["product_coverage"]
    assert coverage["available_stock"] == 80.0
    assert coverage["safety_stock"] == 20.0
    assert coverage["open_purchase_order_quantity"] == 20.0
    assert coverage["open_commitment_quantity"] == 10.0
    assert coverage["projected_balance"] == 90.0
    assert items[0]["request_number"] == "SC001"
    assert items[0]["open_quantity_primary_unit"] == 50.0
    assert "unit_price" not in items[0]
    assert payload["products"][0]["product_coverage"]["safety_stock"] == 20.0


def test_coverage_includes_estseg_product_without_open_request() -> None:
    payload = build_purchase_request_open_coverage(
        requests=[],
        stocks=[
            {
                "product_code": "10020113",
                "product_description": "Cobre",
                "unit": "KG",
                "available_stock": 10.0,
                "safety_stock": 40.0,
            }
        ],
        orders=[],
        commitments=[],
    )
    assert payload["items"] == []
    assert payload["products"][0]["product_code"] == "10020113"
    assert payload["products"][0]["product_coverage"]["safety_stock"] == 40.0
    assert payload["products"][0]["product_coverage"]["projected_balance"] == 10.0


def test_use_case_skips_orders_when_there_are_no_requests_or_products() -> None:
    repository = MagicMock()
    repository.fetch_open_purchase_requests_for_branch.return_value = []
    repository.fetch_available_stock_for_open_purchase_request_products.return_value = []
    result = GetPurchaseRequestsOpenCoverageUseCase(repository).execute(branch="01")
    assert result == {"items": [], "products": []}
    repository.fetch_available_stock_for_open_purchase_request_products.assert_called_once_with(
        branch="01"
    )
    repository.fetch_open_purchase_orders_for_branch.assert_not_called()
    repository.fetch_open_commitments_for_branch.assert_not_called()


def test_use_case_assembles_dump_from_four_branch_queries() -> None:
    repository = MagicMock()
    repository.fetch_open_purchase_requests_for_branch.return_value = [
        {
            "branch": "01",
            "request_number": "SC001",
            "request_item": "01",
            "product_code": "10020113",
            "product_description": "Cobre",
            "warehouse": "01",
            "unit": "KG",
            "open_quantity": 12.0,
        }
    ]
    repository.fetch_available_stock_for_open_purchase_request_products.return_value = [
        {"product_code": "10020113", "unit": "KG", "available_stock": 4.0}
    ]
    repository.fetch_open_purchase_orders_for_branch.return_value = []
    repository.fetch_open_commitments_for_branch.return_value = []

    result = GetPurchaseRequestsOpenCoverageUseCase(repository).execute(branch="01")
    assert result["items"][0]["product_coverage"]["projected_balance"] == 4.0
    assert result["products"][0]["product_coverage"]["safety_stock"] == 0.0
    repository.fetch_open_purchase_requests_for_branch.assert_called_once_with(branch="01")
    repository.fetch_available_stock_for_open_purchase_request_products.assert_called_once_with(
        branch="01"
    )


@pytest.fixture
def purchase_requests_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.purchase_requests_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch(
    "app.interface.http.routes.supplies.purchase_requests_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.supplies.purchase_requests_router.build_get_purchase_requests_open_coverage_use_case"
)
def test_open_coverage_returns_envelope(
    mock_builder,
    _mock_branch,
    purchase_requests_client: TestClient,
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [{"request_number": "SC001"}]}
    mock_builder.return_value = use_case

    response = purchase_requests_client.get(
        "/supplies/purchase-requests/open-coverage",
        params={"branch": "01"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_supplies_purchase_requests_open_coverage"
    assert body["meta"]["entity"] == "supplies_purchase_request_coverage"
    assert body["meta"]["shape"] == "list"
    assert body["data"]["items"][0]["request_number"] == "SC001"
    use_case.execute.assert_called_once_with(branch="01")


@patch(
    "app.interface.http.routes.supplies.purchase_requests_router.branch_access_error",
)
def test_open_coverage_denies_branch_without_permission(
    mock_branch,
    purchase_requests_client: TestClient,
) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar estoque de segurança desta filial.",
        status_code=403,
    )

    response = purchase_requests_client.get(
        "/supplies/purchase-requests/open-coverage",
        params={"branch": "02"},
    )
    body = _body(response)

    assert response.status_code == 403
    assert body["success"] is False
