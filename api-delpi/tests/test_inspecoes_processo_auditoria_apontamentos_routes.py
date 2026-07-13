"""Smoke HTTP — auditoria de apontamentos sem inspeção de processo."""

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
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router.build_list_inspecoes_processo_auditoria_apontamentos_use_case"
)
def test_inspecoes_processo_auditoria_apontamentos_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_auditoria_apontamentos_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "summary": {
            "operadores_pendentes": 1,
            "apontamentos_pendentes": 1,
            "ops_operacoes_pendentes": 1,
            "apontamentos_com_inspecao": 2,
        },
        "items": [
            {
                "filial": "01",
                "cod_operador": "12345",
                "nome_operador": "JOAO",
                "op": "100",
                "operacao": "01",
                "tem_inspecao_amarrada": True,
                "tem_inspecao_executada": False,
            }
        ],
        "page": 1,
        "page_size": 50,
        "has_next": False,
        "data": "2026-07-13",
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_processo_auditoria_apontamentos_route(
        branch="01",
        data="2026-07-13",
        page=1,
        page_size=50,
    )
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_processo_auditoria_apontamentos"
    assert meta.get("shape") == "paged_list"
    assert body["data"]["items"][0]["op"] == "100"
    mock_use_case.execute.assert_called_once_with(
        branch="01",
        data="2026-07-13",
        page=1,
        page_size=50,
    )


@patch(
    "app.interface.http.routes.inspecoes_processo.inspecoes_processo_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_processo_auditoria_apontamentos_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_processo.inspecoes_processo_router import (
        get_inspecoes_processo_auditoria_apontamentos_route,
    )

    response = get_inspecoes_processo_auditoria_apontamentos_route(branch="01")
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


def test_inspecoes_processo_auditoria_apontamentos_requires_branch(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/auditoria-apontamentos"
    )
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_processo_auditoria_apontamentos_rejects_invalid_branch(
    inspecoes_processo_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_processo_client.get(
        f"/inspecoes-processo/auditoria-apontamentos?branch={branch}"
    )
    assert response.status_code == 422


def test_inspecoes_processo_auditoria_apontamentos_rejects_page_size_above_max(
    inspecoes_processo_client: TestClient,
) -> None:
    response = inspecoes_processo_client.get(
        "/inspecoes-processo/auditoria-apontamentos?branch=01&page_size=101"
    )
    assert response.status_code == 422
