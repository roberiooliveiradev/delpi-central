from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def retrabalho_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.retrabalho.retrabalho_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_all_endpoints(retrabalho_client: TestClient) -> None:
    from app.interface.http.routes.retrabalho.retrabalho_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/retrabalhos"
    assert "/retrabalhos/health" in paths
    assert "/retrabalhos/resumo" in paths
    assert "/retrabalhos/rework_cost_pct" in paths
    assert "/retrabalhos/mensal" in paths
    assert "/retrabalhos/detalhes" in paths


def test_resumo_requires_filial(retrabalho_client: TestClient) -> None:
    response = retrabalho_client.get("/retrabalhos/resumo")
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_resumo_use_case"
)
def test_resumo_returns_envelope(mock_builder, _mock_branch, retrabalho_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "totalApontamentos": 10,
        "totalHoras": 1.5,
        "totalCusto": 100.0,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get("/retrabalhos/resumo", params={"filial": "01"})
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_retrabalhos_resumo"
    assert body["meta"]["entity"] == "retrabalho_horas_improdutivas_resumo"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["totalApontamentos"] == 10


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_rework_cost_pct_use_case"
)
def test_rework_cost_pct_returns_envelope(
    mock_builder, _mock_branch, retrabalho_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "rework_cost": 1500.0,
        "rol_with_ipi": 100_000.0,
        "rework_cost_pct": 1.5,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get(
        "/retrabalhos/rework_cost_pct",
        params={"filial": "01", "dataInicio": "2026-06-01", "dataFim": "2026-06-30"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_retrabalhos_rework_cost_pct"
    assert body["meta"]["entity"] == "retrabalho_rework_cost_pct"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["rework_cost_pct"] == 1.5
    assert "rework_cost_pct" in (body["meta"].get("fields") or {})


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_detalhes_use_case"
)
def test_detalhes_returns_paged_meta(mock_builder, _mock_branch, retrabalho_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "pageSize": 25,
        "total": 0,
        "totalPages": 0,
    }
    mock_builder.return_value = use_case

    response = retrabalho_client.get(
        "/retrabalhos/detalhes",
        params={"filial": "01", "page": 1, "pageSize": 25},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_detalhes"
    assert body["meta"]["entity"] == "retrabalho_horas_improdutivas_detalhe"
    assert body["meta"]["shape"] == "paged_list"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
)
def test_resumo_denies_filial_without_permission(mock_branch, retrabalho_client: TestClient) -> None:
    from app.core.responses import error_response

    mock_branch.return_value = error_response(
        "Sem permissão para acessar retrabalhos desta filial.",
        status_code=403,
    )

    response = retrabalho_client.get("/retrabalhos/resumo", params={"filial": "02"})
    body = _body(response)

    assert response.status_code == 403
    assert body["success"] is False


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_health_use_case"
)
def test_health_returns_envelope(mock_builder, retrabalho_client: TestClient) -> None:
    mock_builder.return_value = MagicMock(
        execute=MagicMock(return_value={"status": "ok", "viewAvailable": True})
    )
    response = retrabalho_client.get("/retrabalhos/health")
    body = _body(response)
    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_health"
    assert body["meta"]["shape"] == "scalar"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_filtros_use_case"
)
def test_filtros_returns_envelope(
    mock_builder, _mock_branch, retrabalho_client: TestClient
) -> None:
    mock_builder.return_value = MagicMock(
        execute=MagicMock(return_value={"recursos": [], "centrosCusto": []})
    )
    response = retrabalho_client.get("/retrabalhos/filtros", params={"filial": "01"})
    body = _body(response)
    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_filtros"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_mensal_use_case"
)
def test_mensal_returns_envelope(
    mock_builder, _mock_branch, retrabalho_client: TestClient
) -> None:
    mock_builder.return_value = MagicMock(execute=MagicMock(return_value={"points": []}))
    response = retrabalho_client.get("/retrabalhos/mensal", params={"filial": "01"})
    body = _body(response)
    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_mensal"
    assert body["meta"]["shape"] == "list"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_recursos_use_case"
)
def test_recursos_returns_envelope(
    mock_builder, _mock_branch, retrabalho_client: TestClient
) -> None:
    mock_builder.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = retrabalho_client.get("/retrabalhos/recursos", params={"filial": "01"})
    body = _body(response)
    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_recursos"
    assert body["meta"]["shape"] == "list"


@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.retrabalho.retrabalho_router.build_get_retrabalho_colaboradores_use_case"
)
def test_colaboradores_returns_envelope(
    mock_builder, _mock_branch, retrabalho_client: TestClient
) -> None:
    mock_builder.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = retrabalho_client.get(
        "/retrabalhos/colaboradores", params={"filial": "01"}
    )
    body = _body(response)
    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_retrabalhos_colaboradores"
    assert body["meta"]["shape"] == "list"
