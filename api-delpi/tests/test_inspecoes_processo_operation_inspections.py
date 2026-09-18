"""SQL e smoke — inspeções de processo por OP+operação (sem ensaios)."""

from __future__ import annotations

import inspect
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_operation_inspections_use_case import (
    ListInspecoesProcessoOperationInspectionsUseCase,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    InspecoesProcessoRepository,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def inspections_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_operation_inspections_sql_filters_op_and_operation_without_assay_columns() -> None:
    src = inspect.getsource(InspecoesProcessoRepository.list_operation_inspections)
    assert "historico_tela" in src
    assert "Ordem_Producao" in src
    assert "Operacao" in src
    assert "Nome_Ensaiador" in src
    assert "Data_Medicao_Date" in src
    assert "Hora_Medicao" in src
    assert "GROUP BY" in src
    assert "Codigo_Ensaio" not in src
    assert "Nome_Ensaio" not in src
    assert "Medicao_Numerica" not in src


def test_use_case_returns_sessions_and_empty() -> None:
    repo = MagicMock()
    repo.list_operation_inspections.return_value = [
        {
            "inspector_name": "JOAO",
            "inspector_registration": "0001",
            "measurement_date": "20260910",
            "measurement_time": "08:15",
            "result_code": "A",
            "result": "APROVADO",
        }
    ]
    use_case = ListInspecoesProcessoOperationInspectionsUseCase(repo)
    payload = use_case.execute(
        branch="01",
        production_order="123456001",
        operation="01",
    )
    assert payload["summary"]["inspection_count"] == 1
    assert payload["items"][0]["inspector_name"] == "JOAO"
    assert payload["items"][0]["result_code"] == "A"

    repo.list_operation_inspections.return_value = []
    empty = use_case.execute(
        branch="01",
        production_order="123456001",
        operation="99",
    )
    assert empty["items"] == []
    assert empty["summary"]["inspection_count"] == 0


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router"
    ".build_list_inspecoes_processo_operation_inspections_use_case"
)
@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router"
    ".branch_access_error",
    return_value=None,
)
def test_route_returns_envelope(
    _branch_ok, mock_builder, inspections_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "production_order": "123456001",
        "operation": "01",
        "items": [
            {
                "inspector_name": "JOAO",
                "measurement_date": "2026-09-10",
                "measurement_time": "08:15",
                "result": "APROVADO",
                "result_code": "A",
            }
        ],
        "summary": {"inspection_count": 1},
    }
    mock_builder.return_value = use_case

    response = inspections_client.get(
        "/inspecoes-processo/operations/inspections",
        params={
            "branch": "01",
            "production_order": "123456001",
            "operation": "01",
        },
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "list_inspecoes_processo_operation_inspections"
    assert payload["meta"]["entity"] == "inspecoes_processo_operation_inspections"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["items"][0]["inspector_name"] == "JOAO"
