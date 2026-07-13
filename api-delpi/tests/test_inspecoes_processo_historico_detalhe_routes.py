"""Smoke HTTP — detalhe de OP de inspeções de processo."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_get_inspecoes_processo_historico_detalhe_use_case"
)
def test_inspecoes_processo_historico_detalhe_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_historico_detalhe_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "cabecalho": {"ordem_producao": "10565201002", "filial": "01"},
        "items": [{"codigo_ensaio": "20"}],
        "page": 1,
        "page_size": 100,
        "has_next": False,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_historico_detalhe_route(
        branch="01",
        ordem_producao="10565201002",
        page=1,
        page_size=100,
    )
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_processo_historico_detalhe"
    assert meta.get("shape") == "object"
    assert body["data"]["cabecalho"]["ordem_producao"] == "10565201002"


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_get_inspecoes_processo_historico_detalhe_use_case"
)
def test_inspecoes_processo_historico_detalhe_returns_404(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_historico_detalhe_route,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = None
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_historico_detalhe_route(
        branch="01",
        ordem_producao="missing",
        page=1,
        page_size=100,
    )
    assert response.status_code == 404


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_processo_historico_detalhe_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_historico_detalhe_route,
    )

    response = get_inspecoes_processo_historico_detalhe_route(
        branch="01",
        ordem_producao="10565201002",
        page=1,
        page_size=100,
    )
    assert response.status_code == 403


@pytest.fixture
def inspecoes_processo_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_processo_historico_detalhe_requires_params(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get("/inspecoes-processo/historico/detalhe")
    assert response.status_code == 422


def test_inspecoes_processo_historico_detalhe_requires_ordem_producao(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/historico/detalhe?branch=01"
    )
    assert response.status_code == 422


def test_inspecoes_processo_historico_detalhe_rejects_page_size_above_max(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/historico/detalhe?branch=01&ordem_producao=1&page_size=201"
    )
    assert response.status_code == 422
