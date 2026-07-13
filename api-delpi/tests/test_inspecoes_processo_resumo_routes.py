"""Smoke HTTP — resumo de inspeções de processo."""

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
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_get_inspecoes_processo_resumo_use_case"
)
def test_inspecoes_processo_resumo_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_resumo_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "filial": "01",
        "unidade": "SC",
        "qtde_ops": 10,
        "qtde_ensaios": 100,
        "qtde_ensaios_aprovados": 95,
        "qtde_ensaios_reprovados": 5,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 8,
        "qtde_ops_reprovadas": 2,
        "qtde_ops_tolerancia": 0,
        "qtde_ops_nao_identificadas": 0,
        "qtde_produtos": 3,
        "qtde_operacoes": 4,
        "qtde_ensaiadores": 2,
        "primeira_data_medicao": "2024-01-01",
        "ultima_data_medicao": "2026-07-12",
        "percentual_ops_aprovadas": 80.0,
        "percentual_ops_reprovadas": 20.0,
        "percentual_ensaios_aprovados": 95.0,
        "percentual_ensaios_reprovados": 5.0,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_resumo_route(branch="01")
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_processo_resumo"
    assert meta.get("shape") == "scalar"
    assert body.get("data", {}).get("filial") == "01"


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_processo_resumo_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_resumo_route,
    )

    response = get_inspecoes_processo_resumo_route(branch="01")
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


def test_inspecoes_processo_resumo_requires_branch(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get("/inspecoes-processo/resumo")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_processo_resumo_rejects_invalid_branch(
    inspecoes_processo_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_processo_client.get(
        f"/inspecoes-processo/resumo?branch={branch}"
    )
    assert response.status_code == 422
