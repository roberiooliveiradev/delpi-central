"""Smoke HTTP — financeiro inadimplência."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

AGGREGATE_ENDPOINTS = (
    (
        "/financeiro/inadimplencia/resumo",
        "build_get_inadimplencia_resumo_use_case",
        "get_financeiro_inadimplencia_resumo",
        {"totais": {"titulos": 0}},
    ),
    (
        "/financeiro/inadimplencia/mensal",
        "build_get_inadimplencia_mensal_use_case",
        "get_financeiro_inadimplencia_mensal",
        {"items": []},
    ),
    (
        "/financeiro/inadimplencia/faixas-atraso",
        "build_get_inadimplencia_faixas_atraso_use_case",
        "get_financeiro_inadimplencia_faixas_atraso",
        {"items": []},
    ),
)

PAGED_ENDPOINTS = (
    (
        "/financeiro/inadimplencia/clientes",
        "build_get_inadimplencia_clientes_use_case",
        "get_financeiro_inadimplencia_clientes",
    ),
    (
        "/financeiro/inadimplencia/titulos",
        "build_get_inadimplencia_titulos_use_case",
        "get_financeiro_inadimplencia_titulos",
    ),
)

PERIOD_QUERY = "start_date=2025-07-01&end_date=2026-07-01"


@pytest.fixture
def inadimplencia_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.inadimplencia_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints() -> None:
    from app.interface.http.routes.financeiro.inadimplencia_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/financeiro/inadimplencia"
    for path, *_rest in AGGREGATE_ENDPOINTS + PAGED_ENDPOINTS:
        assert path in paths


def test_router_has_permission_decorators() -> None:
    from app.interface.http.routes.financeiro import inadimplencia_router as module

    for name in (
        "get_financeiro_inadimplencia_resumo_route",
        "get_financeiro_inadimplencia_mensal_route",
        "get_financeiro_inadimplencia_faixas_atraso_route",
        "get_financeiro_inadimplencia_clientes_route",
        "get_financeiro_inadimplencia_titulos_route",
    ):
        fn = getattr(module, name)
        assert hasattr(fn, "__wrapped__") or callable(fn)


@pytest.mark.parametrize("path,builder_name,operation_id,payload", AGGREGATE_ENDPOINTS)
@patch(
    "app.interface.http.routes.financeiro.inadimplencia_router.build_get_inadimplencia_resumo_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.inadimplencia_router.build_get_inadimplencia_mensal_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.inadimplencia_router.build_get_inadimplencia_faixas_atraso_use_case"
)
def test_aggregate_endpoints_accept_default_or_custom_period(
    mock_faixas,
    mock_mensal,
    mock_resumo,
    inadimplencia_client: TestClient,
    path: str,
    builder_name: str,
    operation_id: str,
    payload: dict,
) -> None:
    builders = {
        "build_get_inadimplencia_resumo_use_case": mock_resumo,
        "build_get_inadimplencia_mensal_use_case": mock_mensal,
        "build_get_inadimplencia_faixas_atraso_use_case": mock_faixas,
    }
    mock_build = builders[builder_name]
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "periodo": {
            "data_inicio": "2025-07-01",
            "data_fim_exclusiva": "2026-07-01",
            "rotulo": "Últimos 12 meses completos",
        },
        **payload,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response_default = inadimplencia_client.get(path)
    assert response_default.status_code == 200
    body = response_default.json()
    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == operation_id

    response_custom = inadimplencia_client.get(f"{path}?{PERIOD_QUERY}")
    assert response_custom.status_code == 200


def test_partial_period_returns_400(inadimplencia_client: TestClient) -> None:
    response = inadimplencia_client.get(
        "/financeiro/inadimplencia/resumo?start_date=2025-07-01"
    )
    assert response.status_code == 400
    body = response.json()
    assert body.get("success") is False


def test_invalid_period_range_returns_400(inadimplencia_client: TestClient) -> None:
    response = inadimplencia_client.get(
        "/financeiro/inadimplencia/resumo"
        "?start_date=2026-07-01&end_date=2025-07-01"
    )
    assert response.status_code == 400


@pytest.mark.parametrize("path,builder_name,operation_id", PAGED_ENDPOINTS)
@patch(
    "app.interface.http.routes.financeiro.inadimplencia_router.build_get_inadimplencia_clientes_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.inadimplencia_router.build_get_inadimplencia_titulos_use_case"
)
def test_paged_endpoints_return_meta_and_pagination_contract(
    mock_titulos,
    mock_clientes,
    inadimplencia_client: TestClient,
    path: str,
    builder_name: str,
    operation_id: str,
) -> None:
    builders = {
        "build_get_inadimplencia_clientes_use_case": mock_clientes,
        "build_get_inadimplencia_titulos_use_case": mock_titulos,
    }
    mock_build = builders[builder_name]
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "periodo": {
            "data_inicio": "2025-07-01",
            "data_fim_exclusiva": "2026-07-01",
            "rotulo": "Período personalizado",
        },
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total_items": 0,
            "total_pages": 1,
            "has_next": False,
            "has_previous": False,
        },
        "sort": {"sort_by": "late_amount", "sort_dir": "desc"},
        "items": [],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = inadimplencia_client.get(f"{path}?{PERIOD_QUERY}")
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == operation_id
    assert body.get("meta", {}).get("shape") == "paged_list"


def test_page_size_above_maximum_returns_422(
    inadimplencia_client: TestClient,
) -> None:
    response = inadimplencia_client.get(
        f"/financeiro/inadimplencia/titulos?{PERIOD_QUERY}&page_size=101"
    )
    assert response.status_code == 422


def test_invalid_sort_dir_returns_422(inadimplencia_client: TestClient) -> None:
    response = inadimplencia_client.get(
        f"/financeiro/inadimplencia/clientes?{PERIOD_QUERY}&sort_dir=sideways"
    )
    assert response.status_code == 422


def test_invalid_status_returns_422(inadimplencia_client: TestClient) -> None:
    response = inadimplencia_client.get(
        f"/financeiro/inadimplencia/titulos?{PERIOD_QUERY}&status=maybe"
    )
    assert response.status_code == 422


def test_route_contract_registry_contains_operation_ids() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    expected = {
        "get_financeiro_inadimplencia_resumo",
        "get_financeiro_inadimplencia_mensal",
        "get_financeiro_inadimplencia_faixas_atraso",
        "get_financeiro_inadimplencia_clientes",
        "get_financeiro_inadimplencia_titulos",
    }
    assert expected.issubset(ROUTE_CONTRACTS.keys())


def test_main_includes_inadimplencia_router() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    paths = openapi.get("paths", {})
    assert "/financeiro/inadimplencia/resumo" in paths
    assert "/financeiro/inadimplencia/titulos" in paths
