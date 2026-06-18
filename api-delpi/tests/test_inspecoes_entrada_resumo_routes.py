"""Smoke HTTP — resumo de inspeções de entrada."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_get_inspecoes_entrada_resumo_use_case"
)
def test_inspecoes_entrada_resumo_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_resumo_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "pending_inspections": 6,
        "inspected": 731,
        "approved_inspections": 730,
        "rejected_inspections": 1,
        "approval_rate": 99.86,
        "inspections_with_time": 728,
        "average_time_hours": 16.46,
        "average_time_days": 0.69,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_resumo_route(branch="01")
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_resumo"
    assert meta.get("shape") == "scalar"
    assert body.get("data", {}).get("branch") == "01"


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_entrada_resumo_requires_branch(inspecoes_entrada_client: TestClient) -> None:
    response = inspecoes_entrada_client.get("/inspecoes-entrada/resumo")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_resumo_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(f"/inspecoes-entrada/resumo?branch={branch}")
    assert response.status_code == 422
