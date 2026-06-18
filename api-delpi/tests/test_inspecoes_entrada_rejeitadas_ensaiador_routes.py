"""Smoke HTTP — rejeitadas por ensaiador (inspeções de entrada)."""

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
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_rejeitadas_ensaiador_use_case"
)
def test_inspecoes_entrada_rejeitadas_ensaiador_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_rejeitadas_ensaiador_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [
            {
                "branch": "01",
                "inspector_registration": "30006",
                "inspector_name": "NATHALIA FERNANDES SALES",
                "inspector_login": "NATHALIA",
                "rejected_inspections": 1,
            }
        ],
        "total_inspectors": 1,
        "total_rejected": 1,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_rejeitadas_ensaiador_route(branch="01")
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_rejeitadas_ensaiador"
    assert meta.get("shape") == "list"
    assert body.get("data", {}).get("total_inspectors") == 1
    assert body.get("data", {}).get("total_rejected") == 1


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_entrada_rejeitadas_ensaiador_requires_branch(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get("/inspecoes-entrada/rejeitadas-ensaiador")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_rejeitadas_ensaiador_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(
        f"/inspecoes-entrada/rejeitadas-ensaiador?branch={branch}"
    )
    assert response.status_code == 422
