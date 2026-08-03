"""Smoke HTTP — pendências por fornecedor (inspeções de entrada)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_pendentes_fornecedor_use_case"
)
def test_inspecoes_entrada_pendentes_fornecedor_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_pendentes_fornecedor_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [
            {
                "branch": "01",
                "supplier_name": "CRIMPER DO BRASIL IND.E COM. DE TERM E C",
                "pending_count": 3,
            }
        ],
        "total_suppliers": 1,
        "total_pending": 3,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_pendentes_fornecedor_route(branch="01")
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_pendentes_fornecedor"
    assert meta.get("shape") == "list"
    assert body.get("data", {}).get("total_suppliers") == 1
    assert body.get("data", {}).get("total_pending") == 3


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_pendentes_fornecedor_use_case"
)
def test_inspecoes_entrada_pendentes_fornecedor_allows_omit_branch(mock_build, _access, inspecoes_entrada_client: TestClient) -> None:
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {'branch': 'all', 'items': [], 'total_suppliers': 0, 'total_pending': 0}
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = inspecoes_entrada_client.get('/inspecoes-entrada/pendentes-fornecedor')
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert body.get("data", {}).get("branch") == "all"



@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_pendentes_fornecedor_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(
        f"/inspecoes-entrada/pendentes-fornecedor?branch={branch}"
    )
    assert response.status_code == 422
