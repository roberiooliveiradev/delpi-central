from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def retrabalho_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.retrabalho.retrabalho_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints(retrabalho_client: TestClient) -> None:
    from app.interface.http.routes.retrabalho.retrabalho_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/retrabalhos"
    assert "/retrabalhos/health" in paths
    assert "/retrabalhos/resumo" in paths
    assert "/retrabalhos/mensal" in paths
    assert "/retrabalhos/detalhes" in paths


def test_resumo_requires_filial(retrabalho_client: TestClient) -> None:
    response = retrabalho_client.get("/retrabalhos/resumo")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_resumo_use_case"
)
def test_resumo_returns_envelope(mock_builder, _mock_branch, retrabalho_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "totalApontamentos": 10,
        "totalHoras": 1.5,
        "totalCusto": 100.0,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get("/retrabalhos/resumo", params={"filial": "01"})
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_retrabalhos_resumo"
    assert body["meta"]["entity"] == "retrabalho_horas_improdutivas_resumo"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["totalApontamentos"] == 10


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_detalhes_use_case"
)
def test_detalhes_returns_paged_meta(mock_builder, _mock_branch, retrabalho_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "pageSize": 25,
        "total": 0,
        "totalPages": 0,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get(
        "/retrabalhos/detalhes",
        params={"filial": "01", "page": 1, "pageSize": 25},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_detalhes"
    assert body["meta"]["entity"] == "retrabalho_horas_improdutivas_detalhe"
    assert body["meta"]["shape"] == "paged_list"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
)
def test_resumo_denies_filial_without_permission(mock_branch, retrabalho_client: TestClient) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar retrabalhos desta filial.",
        status_code=403,
    )

    response = retrabalho_client.get("/retrabalhos/resumo", params={"filial": "02"})
    body = _body(response)

    assert response.status_code == 403
    assert body["success"] is False
