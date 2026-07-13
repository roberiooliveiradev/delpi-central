"""Smoke HTTP — ranking por produto de inspeções de processo."""

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
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_list_inspecoes_processo_por_produto_use_case"
)
def test_inspecoes_processo_por_produto_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_por_produto_route,
    )

    mock_item = MagicMock()
    mock_item.to_dict.return_value = {
        "filial": "01",
        "unidade": "SC",
        "codigo_produto": "50232464",
        "descricao_produto": "CF20VERM",
        "revisao_produto": "05",
        "qtde_ops": 79,
        "qtde_ensaios": 1416,
        "qtde_ensaios_aprovados": 1194,
        "qtde_ensaios_reprovados": 222,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 8,
        "qtde_ops_reprovadas": 71,
        "qtde_ops_tolerancia": 0,
        "qtde_ensaios_distintos": 14,
        "qtde_operacoes": 3,
        "qtde_ensaiadores": 18,
        "primeira_data_medicao": "2025-02-19",
        "ultima_data_medicao": "2025-06-24",
        "percentual_ops_aprovadas": 10.13,
        "percentual_ops_reprovadas": 89.87,
        "percentual_ensaios_aprovados": 84.32,
        "percentual_ensaios_reprovados": 15.68,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = [mock_item]
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_por_produto_route(branch="01", limit=10)
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_processo_por_produto"
    assert meta.get("shape") == "list"
    assert isinstance(body.get("data"), list)
    assert body["data"][0]["codigo_produto"] == "50232464"
    mock_use_case.execute.assert_called_once_with(branch="01", limit=10)


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_processo_por_produto_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_por_produto_route,
    )

    response = get_inspecoes_processo_por_produto_route(branch="01", limit=10)
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


def test_inspecoes_processo_por_produto_requires_branch(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get("/inspecoes-processo/por-produto")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_processo_por_produto_rejects_invalid_branch(
    inspecoes_processo_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_processo_client.get(
        f"/inspecoes-processo/por-produto?branch={branch}"
    )
    assert response.status_code == 422


def test_inspecoes_processo_por_produto_rejects_limit_above_max(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/por-produto?branch=01&limit=51"
    )
    assert response.status_code == 422
