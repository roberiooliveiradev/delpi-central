from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION
from app.core.responses import error_response


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def refugos_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.refugos.refugos_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints(refugos_client: TestClient) -> None:
    from app.interface.http.routes.refugos.refugos_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/refugos"
    assert "/refugos/health" in paths
    assert "/refugos/resumo" in paths
    assert "/refugos/rankings" in paths
    assert "/refugos/registros" in paths
    assert "/refugos/filtros" in paths


def test_resumo_requires_filial(refugos_client: TestClient) -> None:
    response = refugos_client.get("/refugos/resumo")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.refugos.refugos_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.refugos.refugos_router.build_get_refugos_resumo_use_case"
)
def test_resumo_returns_envelope(mock_builder, _mock_branch, refugos_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "totalValor": 10.5,
        "valorDia": 1.2,
        "valorMes": 10.5,
    }
    mock_builder.return_value = use_case

    response = refugos_client.get("/refugos/resumo", params={"filial": "01"})
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_refugos_resumo"
    assert body["meta"]["entity"] == "refugos_resumo"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["totalValor"] == 10.5


@patch(
    "app.interface.http.routes.refugos.refugos_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.refugos.refugos_router.build_get_refugos_rankings_use_case"
)
def test_rankings_returns_playbook_meta(
    mock_builder, _mock_branch, refugos_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "dimension": "motivo",
        "items": [{"code": "M3", "label": "SETUP", "value": 10.0}],
    }
    mock_builder.return_value = use_case

    response = refugos_client.get(
        "/refugos/rankings",
        params={"filial": "01", "dimension": "motivo"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_refugos_rankings"
    assert body["meta"]["entity"] == "refugos_rankings"
    assert body["meta"]["shape"] == "playbook_report"


@patch(
    "app.interface.http.routes.refugos.refugos_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.refugos.refugos_router.build_get_refugos_registros_use_case"
)
def test_registros_returns_paged_meta(
    mock_builder, _mock_branch, refugos_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "pageSize": 25,
        "total": 0,
        "totalPages": 0,
    }
    mock_builder.return_value = use_case

    response = refugos_client.get(
        "/refugos/registros",
        params={"filial": "01", "page": 1, "pageSize": 25},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_refugos_registros"
    assert body["meta"]["entity"] == "refugos_registros"
    assert body["meta"]["shape"] == "paged_list"


@patch(
    "app.interface.http.routes.refugos.refugos_router.branch_access_error",
    return_value=error_response("Sem permissão", status_code=403),
)
def test_resumo_returns_403_when_branch_denied(
    _mock_branch, refugos_client: TestClient
) -> None:
    response = refugos_client.get("/refugos/resumo", params={"filial": "02"})
    assert response.status_code == 403
