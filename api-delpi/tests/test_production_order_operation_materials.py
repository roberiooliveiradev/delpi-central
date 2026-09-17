"""SQL e smoke — materiais SD4 da OP+operação."""

from __future__ import annotations

import inspect
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.application.use_cases.production.list_production_order_operation_materials_use_case import (
    ListProductionOrderOperationMaterialsUseCase,
)
from app.application.dto.production.list_production_order_operation_materials_request import (
    ListProductionOrderOperationMaterialsRequest,
)
from app.infrastructure.persistence.totvs.production_repositories.production_orders_repository import (
    ProductionOrdersRepository,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def materials_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.production_operational_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_operation_materials_sql_filters_op_and_operation_without_sg1() -> None:
    src = inspect.getsource(ProductionOrdersRepository.fetch_operation_materials)
    assert "SD4010" in src
    assert "RE.D4_OP" in src
    assert "RE.D4_OPERAC" in src
    assert "RE.D4_QTDEORI" in src
    assert "RE.D4_QUANT" in src
    assert "RE.D4_COD" in src
    assert "SG1010" not in src
    assert "JOIN SG" not in src
    assert "FROM SG" not in src
    assert "D_E_L_E_T_ = ''" in src
    assert "GROUP BY" in src
    assert "commitment_count" in src


def test_use_case_aggregates_and_returns_empty() -> None:
    repo = MagicMock()
    repo.fetch_operation_materials.return_value = [
        {
            "product_code": "10080001",
            "description": "Terminal",
            "unit": "PC",
            "original_qty": 10.0,
            "open_qty": 4.0,
            "consumed_qty": 6.0,
            "commitment_count": 2,
        }
    ]
    use_case = ListProductionOrderOperationMaterialsUseCase(repo)
    payload = use_case.execute(
        ListProductionOrderOperationMaterialsRequest(
            production_order="123456001",
            operation="01",
            branch="01",
        )
    )
    assert payload["summary"]["material_count"] == 1
    assert payload["summary"]["commitment_count"] == 2
    assert payload["items"][0]["product_code"] == "10080001"
    assert payload["items"][0]["original_qty"] == 10.0
    assert payload["items"][0]["open_qty"] == 4.0
    assert payload["items"][0]["consumed_qty"] == 6.0

    repo.fetch_operation_materials.return_value = []
    empty = use_case.execute(
        ListProductionOrderOperationMaterialsRequest(
            production_order="123456001",
            operation="02",
            branch="01",
        )
    )
    assert empty["items"] == []
    assert empty["summary"]["material_count"] == 0
    assert repo.fetch_operation_materials.call_args.kwargs["operation"] == "02"


@patch(
    "app.interface.http.routes.production.production_operational_router"
    ".build_list_production_order_operation_materials_use_case"
)
def test_route_returns_envelope(mock_builder, materials_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "production_order": "123456001",
        "operation": "01",
        "items": [
            {
                "product_code": "10080001",
                "description": "Terminal",
                "unit": "PC",
                "original_qty": 10.0,
                "open_qty": 4.0,
                "consumed_qty": 6.0,
                "commitment_count": 2,
            }
        ],
        "summary": {"material_count": 1, "commitment_count": 2},
    }
    mock_builder.return_value = use_case

    response = materials_client.get(
        "/production/orders/123456001/operations/01/materials",
        params={"branch": "01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "list_production_order_operation_materials"
    assert payload["meta"]["entity"] == "production_order_operation_materials"
    assert payload["meta"]["shape"] == "playbook_report"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["items"][0]["product_code"] == "10080001"


@patch(
    "app.interface.http.routes.production.production_operational_router"
    ".build_list_production_order_operation_materials_use_case"
)
def test_route_empty_items_still_ok(mock_builder, materials_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "production_order": "123456001",
        "operation": "99",
        "items": [],
        "summary": {"material_count": 0, "commitment_count": 0},
    }
    mock_builder.return_value = use_case

    response = materials_client.get(
        "/production/orders/123456001/operations/99/materials",
        params={"branch": "01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["data"]["items"] == []
    assert payload["data"]["summary"]["material_count"] == 0
