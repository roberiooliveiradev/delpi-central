"""F3.OVERVIEW — contrato, segurança e resiliência do GET /v1/overview.

Cobre: AuthN (401), AuthZ Core (403 fail-closed), principal humano,
schema versionado, seis indicadores (3 LMP + 3 TRANSFORMA+), metas/IDD
repassados dos owners, filtros (datas/competência/branch), estados
(available/empty/partial/forbidden/unavailable), timeout por família,
delegação do Bearer humano e provenance.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

import engineering_app.interface.http.routes.overview_routes as overview_routes_module
from delpi_auth.service_token import apply_internal_service_headers
from engineering_app.application.models.overview import OverviewIndicator
from engineering_app.application.ports.overview_sources import IndicatorFetch
from engineering_app.application.use_cases.get_engineering_overview import (
    GetEngineeringOverviewUseCase,
)
from engineering_app.main import app

ENGINEERING_ACCESS = "engineering.access"
OTHER_PERMISSION = "my-requests.access"

LMP_IDS = ("lmp_on_time", "lmp_lead_time", "lmp_total_proposals")
TRANSFORMA_IDS = (
    "transforma_gross_savings",
    "transforma_solutions",
    "transforma_roi",
)


@pytest.fixture
def client():
    return TestClient(app)


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Fontes stub — ports falsos, sem rede ---


class _StubFamilySource:
    def __init__(self, system, endpoint, fetch_fn):
        self.system = system
        self.endpoint = endpoint
        self._fetch = fetch_fn

    async def fetch(self, ctx, *, query):
        return await self._fetch(ctx, query=query)


class _StubSiSource:
    system = "api-delpi"
    endpoint = "GET /dashboard/department-indicators"

    def __init__(self, state):
        self._state = state

    async def fetch_scores(self, ctx, *, query):
        self._state["si_queries"].append(query)
        if isinstance(self._state["si"], Exception):
            raise self._state["si"]
        return self._state["si"]


def _indicator(indicator_id, family, **over) -> OverviewIndicator:
    data = {
        "id": indicator_id,
        "label": indicator_id,
        "family": family,
        "availability": "available",
        "value": 1.0,
        "unit": "%",
        "scope": "consolidado",
        "source": "api-delpi",
        "source_endpoint": (
            "GET /engineering/lmps/dashboard/summary"
            if family == "lmp"
            else "GET /engineering/transforma-mais/processes/summary"
        ),
    }
    data.update(over)
    return OverviewIndicator(**data)


def _lmp_indicators():
    return (
        _indicator("lmp_on_time", "lmp", value=92.5, unit="%",
                   has_goal=True, goal_value=90.0),
        _indicator("lmp_lead_time", "lmp", value=7.3, unit="dias úteis"),
        _indicator("lmp_total_proposals", "lmp", value=41.0,
                   unit="propostas"),
    )


def _transforma_indicators():
    return (
        _indicator("transforma_gross_savings", "transforma",
                   value=12500.0, unit="BRL", has_goal=True,
                   goal_value=10000.0, value_prefix="R$ "),
        _indicator("transforma_solutions", "transforma", value=8.0,
                   unit="soluções"),
        _indicator("transforma_roi", "transforma", value=3.4, unit="x"),
    )


@pytest.fixture
def overview_gateways(monkeypatch):
    state = {
        "lmp": IndicatorFetch(status="available",
                              indicators=_lmp_indicators()),
        "transforma": IndicatorFetch(
            status="available", indicators=_transforma_indicators()
        ),
        "si": None,
        "si_queries": [],
        "queries": {},
        "contexts": [],
        "timeout": 0.5,
    }

    def _capture(family):
        async def _fetch(ctx, *, query):
            state["contexts"].append((family, ctx))
            state["queries"][family] = query
            result = state[family]
            if isinstance(result, Exception):
                raise result
            return result

        return _fetch

    def _builder():
        return GetEngineeringOverviewUseCase(
            lmp_source=_StubFamilySource(
                "api-delpi", "GET /engineering/lmps/dashboard/summary",
                _capture("lmp"),
            ),
            transforma_source=_StubFamilySource(
                "api-delpi",
                "GET /engineering/transforma-mais/processes/summary",
                _capture("transforma"),
            ),
            si_source=_StubSiSource(state),
            source_timeout_seconds=state["timeout"],
            max_concurrent_sources=3,
        )

    monkeypatch.setattr(
        overview_routes_module,
        "build_get_engineering_overview_use_case",
        _builder,
    )
    return state


# --- AuthN / AuthZ ---


def test_overview_requires_auth(client):
    response = client.get("/v1/overview")
    assert response.status_code == 401


def test_overview_without_engineering_access_denied(
    client, jwks_env, core_rbac, overview_gateways
):
    core_rbac["behavior"] = ("data", {"permissions": []})
    token = jwks_env["make_token"]()
    response = client.get("/v1/overview", headers=_bearer(token))
    assert response.status_code == 403


def test_overview_sibling_permission_denied(
    client, jwks_env, core_rbac, overview_gateways
):
    core_rbac["behavior"] = (
        "data",
        {"permissions": [OTHER_PERMISSION]},
    )
    token = jwks_env["make_token"]()
    response = client.get("/v1/overview", headers=_bearer(token))
    assert response.status_code == 403


def test_overview_service_principal_denied(
    client, monkeypatch, overview_gateways
):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-1")
    headers = {}
    apply_internal_service_headers(headers)
    response = client.get("/v1/overview", headers=headers)
    assert response.status_code == 403


def test_overview_core_unavailable_fail_closed(
    client, jwks_env, core_rbac, overview_gateways
):
    core_rbac["behavior"] = ("raise", RuntimeError("core down"))
    token = jwks_env["make_token"]()
    response = client.get("/v1/overview", headers=_bearer(token))
    assert response.status_code in (401, 403, 503)


# --- Contrato ---


def test_overview_contract_and_six_indicators(
    client, jwks_env, core_rbac, overview_gateways
):
    token = jwks_env["make_token"]()
    response = client.get("/v1/overview", headers=_bearer(token))
    assert response.status_code == 200
    body = response.json()
    data = body["data"]

    assert data["schema_version"] == "1.0"
    assert data["status"] == "available"
    assert body["meta"]["operationId"] == "get_engineering_overview"
    assert "generated_at" in data

    by_id = {ind["id"]: ind for ind in data["indicators"]}
    assert set(by_id) == set(LMP_IDS) | set(TRANSFORMA_IDS)

    lmp_on_time = by_id["lmp_on_time"]
    assert lmp_on_time["value"] == 92.5
    assert lmp_on_time["unit"] == "%"
    assert lmp_on_time["has_goal"] is True
    assert lmp_on_time["goal_value"] == 90.0
    assert lmp_on_time["source"] == "api-delpi"
    assert "lmps/dashboard/summary" in lmp_on_time["source_endpoint"]

    roi = by_id["transforma_roi"]
    assert roi["value"] == 3.4
    assert roi["unit"] == "x"
    assert "transforma-mais/processes/summary" in roi["source_endpoint"]


def test_overview_idd_attached_from_si(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["si"] = {
        "engineering-projects-on-time": 94.0,
        "engineering-transforma-plus": 88.0,
    }
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]
    by_id = {ind["id"]: ind for ind in data["indicators"]}
    assert by_id["lmp_on_time"]["idd"] == 94.0
    assert (
        by_id["lmp_on_time"]["idd_label"] == "engineering-projects-on-time"
    )
    assert by_id["transforma_gross_savings"]["idd"] == 88.0
    assert by_id["lmp_lead_time"]["idd"] is None


def test_overview_si_failure_keeps_indicators(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["si"] = RuntimeError("si down")
    token = jwks_env["make_token"]()
    response = client.get("/v1/overview", headers=_bearer(token))
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["status"] == "available"
    assert all(ind["idd"] is None for ind in data["indicators"])


# --- Filtros ---


def test_overview_filters_validated_and_forwarded(
    client, jwks_env, core_rbac, overview_gateways
):
    token = jwks_env["make_token"]()
    response = client.get(
        "/v1/overview?start_date=2026-10-01&end_date=2026-10-31"
        "&competence=2026-10&branch=01",
        headers=_bearer(token),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["filters"] == {
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "competence": "2026-10",
        "branch": "01",
    }
    query = overview_gateways["queries"]["lmp"]
    assert query.start_date == "2026-10-01"
    assert query.branch == "01"


@pytest.mark.parametrize(
    "params",
    [
        "start_date=31-10-2026",
        "end_date=2026/10/31",
        "start_date=2026-10-31&end_date=2026-10-01",
        "competence=2026-13",
        "competence=outubro",
    ],
)
def test_overview_invalid_filters_400(
    client, jwks_env, core_rbac, overview_gateways, params
):
    token = jwks_env["make_token"]()
    response = client.get(f"/v1/overview?{params}", headers=_bearer(token))
    assert response.status_code == 400


# --- Estados ---


def test_overview_partial_when_one_family_fails(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["transforma"] = IndicatorFetch(
        status="unavailable", reason="timeout",
        message="Fonte oficial excedeu o tempo limite.",
    )
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]

    assert data["status"] == "partial"
    by_id = {ind["id"]: ind for ind in data["indicators"]}
    # LMP preservado com valores reais.
    assert by_id["lmp_on_time"]["availability"] == "available"
    assert by_id["lmp_on_time"]["value"] == 92.5
    # TRANSFORMA+ indisponível — sem valor inventado.
    for ind_id in TRANSFORMA_IDS:
        assert by_id[ind_id]["availability"] == "unavailable"
        assert by_id[ind_id]["value"] is None
        assert by_id[ind_id]["reason"] == "timeout"


def test_overview_forbidden_family_preserved(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["lmp"] = IndicatorFetch(
        status="forbidden", message="Acesso negado pelo owner da fonte."
    )
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]

    assert data["status"] == "partial"
    by_id = {ind["id"]: ind for ind in data["indicators"]}
    for ind_id in LMP_IDS:
        assert by_id[ind_id]["availability"] == "forbidden"
        assert by_id[ind_id]["value"] is None
    assert by_id["transforma_roi"]["availability"] == "available"


def test_overview_unavailable_when_all_families_fail(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["lmp"] = IndicatorFetch(
        status="unavailable", reason="transport_error"
    )
    overview_gateways["transforma"] = IndicatorFetch(
        status="forbidden", message="negado"
    )
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]

    assert data["status"] == "unavailable"
    assert all(
        ind["value"] is None for ind in data["indicators"]
    )
    assert len(data["indicators"]) == 6


def test_overview_empty_family_reports_empty(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["lmp"] = IndicatorFetch(status="empty")
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]

    by_id = {ind["id"]: ind for ind in data["indicators"]}
    for ind_id in LMP_IDS:
        assert by_id[ind_id]["availability"] == "empty"
        assert by_id[ind_id]["value"] is None


def test_overview_family_timeout_is_unavailable(
    client, jwks_env, core_rbac, overview_gateways
):
    overview_gateways["lmp"] = asyncio.TimeoutError()
    token = jwks_env["make_token"]()
    data = client.get("/v1/overview", headers=_bearer(token)).json()["data"]

    assert data["status"] == "partial"
    by_id = {ind["id"]: ind for ind in data["indicators"]}
    assert by_id["lmp_on_time"]["availability"] == "unavailable"
    assert by_id["transforma_roi"]["availability"] == "available"


# --- Delegação humana ---


def test_overview_delegates_human_token(
    client, jwks_env, core_rbac, overview_gateways
):
    core_rbac["behavior"] = (
        "data",
        {"permissions": [ENGINEERING_ACCESS], "id": "user-deleg-1"},
    )
    token = jwks_env["make_token"](sub="user-deleg-1")
    response = client.get("/v1/overview", headers=_bearer(token))
    assert response.status_code == 200
    assert overview_gateways["contexts"]
    for _family, ctx in overview_gateways["contexts"]:
        assert ctx.access_token == token
        assert ctx.user_id == "user-deleg-1"
        assert ctx.request_id


def test_overview_openapi_contract(client):
    spec = client.get("/openapi.json").json()
    op = spec["paths"]["/v1/overview"]["get"]
    assert op["operationId"] == "get_engineering_overview"
    param_names = {
        p["name"] for p in op.get("parameters", [])
    }
    assert {"start_date", "end_date", "competence", "branch"} <= param_names
