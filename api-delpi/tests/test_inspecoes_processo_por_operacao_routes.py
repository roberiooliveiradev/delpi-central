"""Smoke HTTP — ranking por operação de inspeções de processo."""

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
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_list_inspecoes_processo_por_operacao_use_case"
)
def test_inspecoes_processo_por_operacao_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_por_operacao_route,
    )

    mock_item = MagicMock()
    mock_item.to_dict.return_value = {
        "filial": "01",
        "unidade": "SC",
        "codigo_produto": "50232465",
        "descricao_produto": "CF20AZUL",
        "revisao_produto": "02",
        "roteiro": "01",
        "operacao": "01",
        "recurso": "CT-01A",
        "ferramenta": "23-022",
        "centro_trabalho": "CT-01A",
        "descricao_operacao": "CORTAR E APLICAR 100",
        "qtde_ops": 474,
        "qtde_ensaios": 4908,
        "qtde_ensaios_aprovados": 4714,
        "qtde_ensaios_reprovados": 194,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 317,
        "qtde_ops_reprovadas": 157,
        "qtde_ops_tolerancia": 0,
        "qtde_ensaios_distintos": 8,
        "qtde_ensaiadores": 26,
        "primeira_data_medicao": "2024-11-08",
        "ultima_data_medicao": "2026-07-11",
        "percentual_ops_aprovadas": 66.88,
        "percentual_ops_reprovadas": 33.12,
        "percentual_ensaios_aprovados": 96.05,
        "percentual_ensaios_reprovados": 3.95,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = [mock_item]
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_por_operacao_route(branch="01", limit=10)
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_processo_por_operacao"
    assert meta.get("shape") == "list"
    assert isinstance(body.get("data"), list)
    assert body["data"][0]["operacao"] == "01"
    mock_use_case.execute.assert_called_once_with(branch="01", limit=10)


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_processo_por_operacao_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_por_operacao_route,
    )

    response = get_inspecoes_processo_por_operacao_route(branch="01", limit=10)
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


def test_inspecoes_processo_por_operacao_requires_branch(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get("/inspecoes-processo/por-operacao")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_processo_por_operacao_rejects_invalid_branch(
    inspecoes_processo_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_processo_client.get(
        f"/inspecoes-processo/por-operacao?branch={branch}"
    )
    assert response.status_code == 422


def test_inspecoes_processo_por_operacao_rejects_limit_above_max(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/por-operacao?branch=01&limit=51"
    )
    assert response.status_code == 422
