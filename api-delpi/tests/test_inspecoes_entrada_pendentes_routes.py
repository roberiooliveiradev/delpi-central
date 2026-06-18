"""Smoke HTTP — inspeções pendentes de entrada."""

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
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_pendentes_use_case"
)
def test_inspecoes_entrada_pendentes_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_pendentes_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [
            {
                "branch": "01",
                "received_date": "2026-06-17",
                "received_time": "17:11",
                "invoice_number": "000191170",
                "supplier_code": "000180",
                "supplier_store": "01",
                "supplier_name": "CRIMPER DO BRASIL IND.E COM. DE TERM E C",
                "product_code": "10080026",
                "quantity": 4000.0,
                "unit": "PC",
                "status_code": "",
                "inspection_status": "NAO_IDENTIFICADA",
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 6,
            "total_pages": 1,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_pendentes_route(branch="01", page=1, page_size=10)
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_pendentes"
    assert meta.get("shape") == "paged_list"
    assert body.get("data", {}).get("branch") == "01"
    assert len(body.get("data", {}).get("items", [])) == 1
    assert body.get("data", {}).get("pagination", {}).get("total") == 6


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_entrada_pendentes_requires_branch(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get("/inspecoes-entrada/pendentes")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_pendentes_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(
        f"/inspecoes-entrada/pendentes?branch={branch}"
    )
    assert response.status_code == 422
