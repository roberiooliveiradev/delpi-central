"""Smoke HTTP — histórico de inspeções de entrada."""

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
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_historico_use_case"
)
def test_inspecoes_entrada_historico_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [
            {
                "branch": "01",
                "inspection_id": "01|000042999|2|0002|000532|01|10110388|AUTO000952",
                "result": "REJEITADA",
                "is_rejected": True,
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 731,
            "total_pages": 74,
        },
        "filters": {
            "result": "REJEITADA",
            "date_from": None,
            "date_to": None,
            "supplier": None,
            "product_code": None,
            "inspector": None,
            "invoice_number": None,
            "lot": None,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_route(
        branch="01",
        page=1,
        page_size=10,
        result="REJEITADA",
        date_from=None,
        date_to=None,
        supplier=None,
        product_code=None,
        inspector=None,
        invoice_number=None,
        lot=None,
    )
    body = _body(response)

    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("operationId") == "get_inspecoes_entrada_historico"
    assert meta.get("shape") == "paged_list"
    assert body.get("data", {}).get("branch") == "01"
    assert len(body.get("data", {}).get("items", [])) == 1
    assert body.get("data", {}).get("pagination", {}).get("total") == 731
    assert body.get("data", {}).get("filters", {}).get("result") == "REJEITADA"


@pytest.fixture
def inspecoes_entrada_client() -> TestClient:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_inspecoes_entrada_historico_requires_branch(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get("/inspecoes-entrada/historico")
    assert response.status_code == 422


@pytest.mark.parametrize("branch", ["03", "1", "xx"])
def test_inspecoes_entrada_historico_rejects_invalid_branch(
    inspecoes_entrada_client: TestClient,
    branch: str,
) -> None:
    response = inspecoes_entrada_client.get(
        f"/inspecoes-entrada/historico?branch={branch}"
    )
    assert response.status_code == 422


def test_inspecoes_entrada_historico_rejects_page_size_above_max(
    inspecoes_entrada_client: TestClient,
) -> None:
    response = inspecoes_entrada_client.get(
        "/inspecoes-entrada/historico?branch=01&page_size=201"
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_historico_use_case"
)
def test_inspecoes_entrada_historico_returns_422_for_invalid_result(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_route,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.side_effect = ValueError("result inválido. Use APROVADA ou REJEITADA.")
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_route(
        branch="01",
        page=1,
        page_size=10,
        result="INVALIDO",
        date_from=None,
        date_to=None,
        supplier=None,
        product_code=None,
        inspector=None,
        invoice_number=None,
        lot=None,
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_historico_use_case"
)
def test_inspecoes_entrada_historico_returns_422_for_invalid_date_range(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_route,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.side_effect = ValueError(
        "date_from deve ser menor ou igual a date_to."
    )
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_route(
        branch="01",
        page=1,
        page_size=10,
        result=None,
        date_from="2026-06-30",
        date_to="2026-01-01",
        supplier=None,
        product_code=None,
        inspector=None,
        invoice_number=None,
        lot=None,
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=False,
)
def test_inspecoes_entrada_historico_denies_branch_without_permission(
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_route,
    )

    response = get_inspecoes_entrada_historico_route(
        branch="01",
        page=1,
        page_size=10,
        result=None,
        date_from=None,
        date_to=None,
        supplier=None,
        product_code=None,
        inspector=None,
        invoice_number=None,
        lot=None,
    )
    assert response.status_code == 403
