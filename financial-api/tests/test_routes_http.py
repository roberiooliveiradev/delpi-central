"""Rotas HTTP com gateways falsos — envelope, RBAC e tradução de erro."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_app.composition import financial_composer
from financial_app.interface.http.routes.billing_routes import router as billing_router
from financial_app.interface.http.routes.cost_center_routes import router as cost_center_router
from financial_app.interface.http.routes.delinquency_routes import router as delinquency_router
from financial_app.interface.http.routes.indicators_routes import router as indicators_router
from financial_app.interface.http.routes.overview_routes import router as overview_router
from tests.conftest import full_user
from tests.fakes import FakeFinancialGateway, FakeStrategicIndicatorsGateway


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Monta o app só com os routers, injetando usuário e gateways falsos."""
    state: dict[str, object] = {"user": full_user()}
    financial_gateway = FakeFinancialGateway()
    indicators_gateway = FakeStrategicIndicatorsGateway()

    monkeypatch.setattr(
        financial_composer, "build_financial_gateway", lambda: financial_gateway
    )
    monkeypatch.setattr(
        financial_composer, "build_strategic_indicators_gateway", lambda: indicators_gateway
    )

    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = state["user"]
        return await call_next(request)

    for router in (
        delinquency_router,
        cost_center_router,
        indicators_router,
        overview_router,
        billing_router,
    ):
        app.include_router(router)

    test_client = TestClient(app)
    test_client.state = state  # type: ignore[attr-defined]
    test_client.financial_gateway = financial_gateway  # type: ignore[attr-defined]
    return test_client


@pytest.mark.parametrize(
    "path",
    [
        "/delinquency/dashboard",
        "/delinquency/summary",
        "/delinquency/monthly",
        "/delinquency/aging",
        "/delinquency/customers",
        "/delinquency/titles",
        "/cost-centers/filters?branch=01",
        "/cost-centers/summary?branch=01",
        "/cost-centers/series?branch=01",
        "/cost-centers/ranking-cost-centers?branch=01",
        "/cost-centers/ranking-suppliers?branch=01",
        "/cost-centers/entries?branch=01",
        "/indicators/department",
        "/indicators/global",
        "/overview?branch=01",
        "/billing/dashboard?branch=01",
    ],
)
def test_every_route_family_answers_with_the_envelope(client, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], dict)


def test_branch_gate_returns_403(client) -> None:
    from tests.conftest import user

    client.state["user"] = user(
        "financial.access", "financial.cost-centers.view", "financial.view.filial-01"
    )
    response = client.get("/cost-centers/summary?branch=02")

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_missing_module_permission_returns_403(client) -> None:
    from tests.conftest import user

    client.state["user"] = user("financial.access")
    assert client.get("/delinquency/summary").status_code == 403
    assert client.get("/indicators/department").status_code == 403


def test_invalid_billing_granularity_returns_400(client) -> None:
    response = client.get("/billing/dashboard?branch=01&granularity=quarter")

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_invalid_branch_returns_400(client) -> None:
    response = client.get("/cost-centers/summary?branch=99")

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_half_open_period_returns_400(client) -> None:
    response = client.get("/delinquency/summary?startDate=2026-01-01")

    assert response.status_code == 400
    assert "início e fim" in response.json()["message"]


def test_invalid_sort_returns_400(client) -> None:
    response = client.get("/cost-centers/entries?branch=01&sortBy=drop_table")

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_gateway_outage_returns_502(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from financial_app.domain.errors import DelpiGatewayError

    def explode(**_: object) -> dict:
        raise DelpiGatewayError("api-delpi indisponível")

    monkeypatch.setattr(client.financial_gateway, "fetch_delinquency_summary", explode)
    response = client.get("/delinquency/summary")

    assert response.status_code == 502
    assert response.json()["success"] is False


def test_overview_degrades_without_breaking_the_screen(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(**_: object) -> dict:
        raise RuntimeError("timeout no TOTVS")

    monkeypatch.setattr(client.financial_gateway, "fetch_pmr", explode)
    body = client.get("/overview?branch=01").json()

    blocks = body["data"]["blocks"]
    assert body["success"] is True
    assert blocks["pmr"]["available"] is False
    assert blocks["rol"]["available"] is True
