"""Smoke HTTP — detalhe do histórico de inspeções de entrada."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_get_inspecoes_entrada_historico_detalhe_use_case"
)
def test_inspecoes_entrada_historico_detalhe_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_detalhe_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "inspection_id": "01|000042999|2|0002|000532|01|10110388|AUTO000952",
        "summary": {"result": "REJEITADA", "tests_count": 6, "failed_tests_count": 1},
        "tests": [{"test_code": "000002", "result": "REPROVADO"}],
        "totals": {
            "tests_count": 6,
            "approved_tests_count": 5,
            "failed_tests_count": 1,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_detalhe_route(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_historico_detalhe"
    assert meta.get("shape") == "object"
    assert meta.get("entity") == "inspecoes_entrada_historico_detalhe"
    assert body.get("data", {}).get("inspection_id") == "01|000042999|2|0002|000532|01|10110388|AUTO000952"


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_get_inspecoes_entrada_historico_detalhe_use_case"
)
def test_inspecoes_entrada_historico_detalhe_returns_404_when_not_found(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_detalhe_route,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = None
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_detalhe_route(
        branch="01",
        inspection_id="missing",
    )

    assert response.status_code == 404
    body = _body(response)
    assert body.get("success") is False


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_entrada_historico_detalhe_requires_branch(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get(
        "/inspecoes-entrada/historico/detalhe?inspection_id=01|x"
    )
    assert response.status_code == 422


def test_inspecoes_entrada_historico_detalhe_requires_inspection_id(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get("/inspecoes-entrada/historico/detalhe?branch=01")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_historico_detalhe_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(
        f"/inspecoes-entrada/historico/detalhe?branch={branch}&inspection_id=01|x"
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_entrada_historico_detalhe_returns_403_without_branch_permission(
    _mock_branch,
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get(
        "/inspecoes-entrada/historico/detalhe?branch=01&inspection_id=01|x"
    )
    assert response.status_code == 403
