from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


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
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_resumo_use_case"
)
def test_resumo_returns_envelope(mock_builder, retrabalho_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "totalApontamentos": 10,
        "totalHoras": 1.5,
        "totalCusto": 100.0,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get("/retrabalhos/resumo", params={"filial": "01"})
    body = json.loads(response.content.decode())

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_retrabalhos_resumo"
    assert body["data"]["totalApontamentos"] == 10
