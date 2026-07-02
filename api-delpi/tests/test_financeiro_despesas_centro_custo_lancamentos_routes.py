from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

LANCAMENTOS_PATH = "/financeiro/despesas-centro-custo/lancamentos"
PERIOD_QUERY = "start_date=2025-06-01&end_date=2025-06-30"


@pytest.fixture
def despesas_centro_custo_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.despesas_centro_custo_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_lancamentos_endpoint() -> None:
    from app.interface.http.routes.financeiro.despesas_centro_custo_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert LANCAMENTOS_PATH in paths


def test_lancamentos_requires_period(despesas_centro_custo_client: TestClient) -> None:
    response = despesas_centro_custo_client.get(LANCAMENTOS_PATH)
    assert response.status_code == 422


@pytest.mark.parametrize("query", ("start_date=2025-06-01", "end_date=2025-06-30"))
def test_lancamentos_rejects_partial_period(
    despesas_centro_custo_client: TestClient,
    query: str,
) -> None:
    response = despesas_centro_custo_client.get(f"{LANCAMENTOS_PATH}?{query}")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_lancamentos_use_case"
)
def test_lancamentos_accepts_valid_period_and_returns_meta(
    mock_build,
    despesas_centro_custo_client: TestClient,
) -> None:
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "periodo": {"data_inicio": "20250601", "data_fim": "20250630"},
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total_items": 0,
            "total_pages": 1,
            "has_next": False,
            "has_previous": False,
        },
        "sort": {"sort_by": "data_emissao", "sort_dir": "desc"},
        "items": [],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = despesas_centro_custo_client.get(f"{LANCAMENTOS_PATH}?{PERIOD_QUERY}")

    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == (
        "get_financeiro_despesas_centro_custo_lancamentos"
    )
    assert body.get("meta", {}).get("shape") == "paged_list"


@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_lancamentos_use_case"
)
def test_lancamentos_applies_default_page_and_page_size(
    mock_build,
    despesas_centro_custo_client: TestClient,
) -> None:
    mock_use_case = MagicMock()
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {"items": []}
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    despesas_centro_custo_client.get(f"{LANCAMENTOS_PATH}?{PERIOD_QUERY}")

    request = mock_use_case.execute.call_args.args[0]
    assert request.page == 1
    assert request.page_size == 50


def test_lancamentos_rejects_page_size_above_maximum(
    despesas_centro_custo_client: TestClient,
) -> None:
    response = despesas_centro_custo_client.get(
        f"{LANCAMENTOS_PATH}?{PERIOD_QUERY}&page_size=201"
    )
    assert response.status_code == 422


def test_lancamentos_rejects_invalid_sort_dir(
    despesas_centro_custo_client: TestClient,
) -> None:
    response = despesas_centro_custo_client.get(
        f"{LANCAMENTOS_PATH}?{PERIOD_QUERY}&sort_dir=invalid"
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.financeiro.despesas_centro_custo_router.build_get_despesas_centro_custo_lancamentos_use_case"
)
def test_lancamentos_rejects_sort_by_outside_allowlist(
    mock_build,
    despesas_centro_custo_client: TestClient,
) -> None:
    response = despesas_centro_custo_client.get(
        f"{LANCAMENTOS_PATH}?{PERIOD_QUERY}&sort_by=drop_table"
    )

    assert response.status_code == 400
    mock_build.assert_not_called()


def test_route_contract_registry_contains_lancamentos_operation_id() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    contract = ROUTE_CONTRACTS["get_financeiro_despesas_centro_custo_lancamentos"]
    assert contract.entity == "financeiro_despesas_centro_custo_lancamento"
    assert contract.shape == "paged_list"
