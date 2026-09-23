"""SQL e smoke — materiais SD4 da OP+operação (consulta única e em lote)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.application.use_cases.production.list_production_order_operation_materials_batch_use_case import (
    ListProductionOrderOperationMaterialsBatchUseCase,
)
from app.application.use_cases.production.list_production_order_operation_materials_use_case import (
    ListProductionOrderOperationMaterialsUseCase,
)
from app.application.dto.production.list_production_order_operation_materials_batch_request import (
    ListProductionOrderOperationMaterialsBatchRequest,
)
from app.application.dto.production.list_production_order_operation_materials_request import (
    ListProductionOrderOperationMaterialsRequest,
)
from app.domain.production.operation_materials_scope import (
    MAX_BATCH_PRODUCTION_ORDERS,
)
from app.infrastructure.persistence.totvs.production_repositories.production_order_operation_materials_sql import (
    operation_materials_sql,
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
    src = operation_materials_sql(order_count=1, filter_operation=True)
    assert "SD4010" in src
    assert "RE.D4_OP" in src
    assert "RE.D4_OPERAC" in src
    assert "RE.D4_QTDEORI" in src
    assert "RE.D4_QUANT" in src
    assert "RE.D4_COD" in src
    assert "P.B1_TIPO" in src
    assert "AS product_type" in src
    assert "SG1010" not in src
    assert "JOIN SG" not in src
    assert "FROM SG" not in src
    assert "D_E_L_E_T_ = ''" in src
    assert "GROUP BY" in src
    assert "commitment_count" in src
    # Consulta unitária: igualdade na OP e filtro de operação obrigatório.
    assert "RTRIM(LTRIM(RE.D4_OP)) = ?" in src
    assert "RTRIM(LTRIM(RE.D4_OPERAC)) = ?" in src
    assert src.count("?") == 3


def test_batch_sql_filters_many_orders_without_operation_and_without_sg1() -> None:
    src = operation_materials_sql(order_count=3, filter_operation=False)
    assert "SD4010" in src
    assert "RTRIM(LTRIM(RE.D4_OP)) IN (?, ?, ?)" in src
    # Em lote quem escolhe o par OP+operação é o consumidor: sem filtro D4_OPERAC.
    assert "RTRIM(LTRIM(RE.D4_OPERAC)) = ?" not in src
    # A operação continua projetada e agrupada para o consumidor casar o par.
    assert "RTRIM(LTRIM(RE.D4_OPERAC)) AS operation" in src
    assert "RE.D4_OPERAC," in src
    assert "P.B1_TIPO" in src
    assert "AS product_type" in src
    assert "SG1010" not in src
    assert "JOIN SG" not in src
    assert "FROM SG" not in src
    assert "D_E_L_E_T_ = ''" in src
    # 3 OPs + filial.
    assert src.count("?") == 4


def test_batch_sql_rejects_empty_order_count() -> None:
    with pytest.raises(ValueError):
        operation_materials_sql(order_count=0, filter_operation=False)


def test_repository_batch_passes_orders_then_branch_and_skips_empty() -> None:
    repo = ProductionOrdersRepository()
    with patch.object(
        ProductionOrdersRepository, "execute_query", return_value=[]
    ) as query, patch.object(
        ProductionOrdersRepository, "__enter__", return_value=repo
    ), patch.object(
        ProductionOrdersRepository, "__exit__", return_value=False
    ):
        repo.fetch_operation_materials_batch(
            production_orders=("123456001", "123456002"),
            branch="01",
        )
        assert query.call_args.args[1] == ("123456001", "123456002", "01")

        query.reset_mock()
        assert repo.fetch_operation_materials_batch(
            production_orders=(), branch="01"
        ) == []
        query.assert_not_called()


def test_batch_request_dedupes_trims_and_caps_orders() -> None:
    request = ListProductionOrderOperationMaterialsBatchRequest(
        production_orders=[" 123456001 ", "123456001", "", "123456002"],
        branch="01",
    )
    assert request.production_orders == ("123456001", "123456002")

    with pytest.raises(ValueError):
        ListProductionOrderOperationMaterialsBatchRequest(
            production_orders=[
                f"{index:09d}" for index in range(MAX_BATCH_PRODUCTION_ORDERS + 1)
            ],
            branch="01",
        )


def test_batch_use_case_keeps_op_and_operation_per_item() -> None:
    repo = MagicMock()
    repo.fetch_operation_materials_batch.return_value = [
        {
            "production_order": "123456001",
            "operation": "01",
            "product_code": "10080001",
            "description": "Terminal",
            "unit": "PC",
            "product_type": "mp",
            "original_qty": 10.0,
            "open_qty": 4.0,
            "consumed_qty": 6.0,
            "commitment_count": 2,
        },
        {
            "production_order": "123456002",
            "operation": "02",
            "product_code": "10080002",
            "description": "Cabo",
            "unit": "MT",
            "product_type": "PI",
            "original_qty": 5.0,
            "open_qty": 5.0,
            "consumed_qty": 0.0,
            "commitment_count": 1,
        },
    ]
    use_case = ListProductionOrderOperationMaterialsBatchUseCase(repo)
    payload = use_case.execute(
        ListProductionOrderOperationMaterialsBatchRequest(
            production_orders=["123456001", "123456002"],
            branch="01",
        )
    )
    assert payload["summary"] == {
        "requested_count": 2,
        "returned_count": 2,
        "order_count": 2,
        "commitment_count": 3,
    }
    assert payload["items"][0]["production_order"] == "123456001"
    assert payload["items"][0]["operation"] == "01"
    assert payload["items"][0]["open_qty"] == 4.0
    assert payload["items"][0]["product_type"] == "MP"
    assert payload["items"][1]["product_code"] == "10080002"
    assert payload["items"][1]["product_type"] == "PI"


def test_normalize_operation_material_item_includes_product_type() -> None:
    from app.application.use_cases.production.operation_materials_item import (
        normalize_operation_material_item,
    )

    item = normalize_operation_material_item(
        {
            "product_code": "30190001",
            "description": "Resina",
            "unit": "KG",
            "product_type": " mp ",
            "original_qty": 1.0,
            "open_qty": 1.0,
            "consumed_qty": 0.0,
            "commitment_count": 1,
        }
    )
    assert item["product_type"] == "MP"
    assert "product_type" in item


def test_batch_use_case_without_orders_does_not_touch_repository() -> None:
    repo = MagicMock()
    use_case = ListProductionOrderOperationMaterialsBatchUseCase(repo)
    payload = use_case.execute(
        ListProductionOrderOperationMaterialsBatchRequest(
            production_orders=[],
            branch="01",
        )
    )
    assert payload["items"] == []
    assert payload["summary"]["requested_count"] == 0
    repo.fetch_operation_materials_batch.assert_not_called()


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


@patch(
    "app.interface.http.routes.production.production_operational_router"
    ".build_list_production_order_operation_materials_batch_use_case"
)
def test_batch_route_returns_envelope(
    mock_builder, materials_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "production_orders": ["123456001"],
        "items": [
            {
                "production_order": "123456001",
                "operation": "01",
                "product_code": "10080001",
                "description": "Terminal",
                "unit": "PC",
                "original_qty": 10.0,
                "open_qty": 4.0,
                "consumed_qty": 6.0,
                "commitment_count": 2,
            }
        ],
        "summary": {
            "requested_count": 1,
            "returned_count": 1,
            "order_count": 1,
            "commitment_count": 2,
        },
    }
    mock_builder.return_value = use_case

    response = materials_client.post(
        "/production/orders/operation-materials/batch",
        json={"branch": "01", "production_orders": ["123456001"]},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert (
        payload["meta"]["operationId"]
        == "list_production_order_operation_materials_batch"
    )
    assert (
        payload["meta"]["entity"] == "production_order_operation_materials_batch"
    )
    assert payload["meta"]["shape"] == "list"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["items"][0]["operation"] == "01"


def test_batch_route_rejects_invalid_branch(materials_client: TestClient) -> None:
    response = materials_client.post(
        "/production/orders/operation-materials/batch",
        json={"branch": "09", "production_orders": ["123456001"]},
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.production.production_operational_router"
    ".build_list_production_order_operation_materials_batch_use_case"
)
def test_batch_route_rejects_over_cap(
    mock_builder, materials_client: TestClient
) -> None:
    mock_builder.return_value = MagicMock()
    response = materials_client.post(
        "/production/orders/operation-materials/batch",
        json={
            "branch": "01",
            "production_orders": [
                f"{index:09d}" for index in range(MAX_BATCH_PRODUCTION_ORDERS + 1)
            ],
        },
    )
    assert response.status_code == 400
    assert str(MAX_BATCH_PRODUCTION_ORDERS) in _body(response)["message"]
