"""Smoke HTTP — despesas por centro de custo."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

AGGREGATE_ENDPOINTS = (
    (
        "/financeiro/despesas-centro-custo/resumo",
        "build_get_despesas_centro_custo_resumo_use_case",
        "get_financeiro_despesas_centro_custo_resumo",
        {"total_periodo": 100.0},
    ),
    (
        "/financeiro/despesas-centro-custo/serie",
        "build_get_despesas_centro_custo_serie_use_case",
        "get_financeiro_despesas_centro_custo_serie",
        {"serie": []},
    ),
    (
        "/financeiro/despesas-centro-custo/ranking-centros",
        "build_get_despesas_centro_custo_ranking_centros_use_case",
        "get_financeiro_despesas_centro_custo_ranking_centros",
        {"ranking": []},
    ),
    (
        "/financeiro/despesas-centro-custo/ranking-fornecedores",
        "build_get_despesas_centro_custo_ranking_fornecedores_use_case",
        "get_financeiro_despesas_centro_custo_ranking_fornecedores",
        {"ranking": []},
    ),
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


@pytest.fixture
def despesas_centro_custo_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.despesas_centro_custo_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_aggregate_endpoints() -> None:
    from app.interface.http.routes.financeiro.despesas_centro_custo_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/financeiro/despesas-centro-custo"
    assert "/financeiro/despesas-centro-custo/filtros" in paths
    assert "/financeiro/despesas-centro-custo/lancamentos" in paths
    for path, *_rest in AGGREGATE_ENDPOINTS:
        assert path in paths


@pytest.mark.parametrize(
    "path",
    [item[0] for item in AGGREGATE_ENDPOINTS],
)
def test_aggregate_endpoints_require_period(
    despesas_centro_custo_client: TestClient,
    path: str,
) -> None:
    response = despesas_centro_custo_client.get(path)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "path",
    [item[0] for item in AGGREGATE_ENDPOINTS],
)
def test_aggregate_endpoints_reject_partial_period(
    despesas_centro_custo_client: TestClient,
    path: str,
) -> None:
    for query in ("start_date=2025-06-01", "end_date=2025-06-30"):
        response = despesas_centro_custo_client.get(f"{path}?{query}")
        assert response.status_code == 422


@pytest.mark.parametrize("path,builder_name,operation_id,payload", AGGREGATE_ENDPOINTS)
@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_resumo_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_serie_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_ranking_centros_use_case"
)
@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_ranking_fornecedores_use_case"
)
def test_aggregate_endpoints_accept_valid_period_and_return_meta(
    mock_ranking_fornecedores,
    mock_ranking_centros,
    mock_serie,
    mock_resumo,
    despesas_centro_custo_client: TestClient,
    path: str,
    builder_name: str,
    operation_id: str,
    payload: dict,
) -> None:
    builders = {
        "build_get_despesas_centro_custo_resumo_use_case": mock_resumo,
        "build_get_despesas_centro_custo_serie_use_case": mock_serie,
        "build_get_despesas_centro_custo_ranking_centros_use_case": mock_ranking_centros,
        "build_get_despesas_centro_custo_ranking_fornecedores_use_case": mock_ranking_fornecedores,
    }
    mock_build = builders[builder_name]

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "periodo": {"data_inicio": "20250601", "data_fim": "20250630"},
        **payload,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = despesas_centro_custo_client.get(
        f"{path}?start_date=2025-06-01&end_date=20250630"
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == operation_id


@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_filtros_use_case"
)
def test_financeiro_despesas_centro_custo_filtros_returns_meta(mock_build) -> None:
    from app.interface.http.routes.financeiro.despesas_centro_custo_router import (
        get_financeiro_despesas_centro_custo_filtros_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "periodo": {"data_inicio": "20250601", "data_fim": "20250630"},
        "filiais": [{"codigo": "01"}],
        "centros_custo": [{"codigo": "0101", "descricao": "DIRECAO"}],
        "fornecedores": [
            {
                "codigo": "003287",
                "loja": "01",
                "razao_social": "DELIZIA DI PANE",
            }
        ],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_financeiro_despesas_centro_custo_filtros_route(
        start_date="2025-06-01",
        end_date="2025-06-30",
        branch="01",
    )
    body = _body(response)

    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == (
        "get_financeiro_despesas_centro_custo_filtros"
    )


def test_route_contract_registry_contains_aggregate_operation_ids() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    expected = {
        "get_financeiro_despesas_centro_custo_filtros",
        "get_financeiro_despesas_centro_custo_resumo",
        "get_financeiro_despesas_centro_custo_serie",
        "get_financeiro_despesas_centro_custo_ranking_centros",
        "get_financeiro_despesas_centro_custo_ranking_fornecedores",
        "get_financeiro_despesas_centro_custo_lancamentos",
    }
    assert expected.issubset(ROUTE_CONTRACTS.keys())
