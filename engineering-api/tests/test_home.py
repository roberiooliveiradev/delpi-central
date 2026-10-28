"""F2a.S5 — contrato, segurança e resiliência do GET /v1/home.

Cobre: AuthN (401), AuthZ Core (403/503 fail-closed), principal humano,
schema versionado, estados de seção (available/empty/unavailable/forbidden/
not_implemented), falhas parciais, timeout por fonte, fan-out limitado,
provenance e headers de observabilidade.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

import engineering_app.interface.http.routes.home_routes as home_routes_module
from delpi_auth.service_token import apply_internal_service_headers
from engineering_app.application.models.home import HomeItem
from engineering_app.application.ports.home_sources import SectionFetch
from engineering_app.application.use_cases.get_engineering_home import (
    GetEngineeringHome,
)
from engineering_app.main import app

ENGINEERING_ACCESS = "engineering.access"
OTHER_PERMISSION = "my-requests.access"


@pytest.fixture
def client():
    return TestClient(app)


# --- Fontes stub — ports falsos, sem rede ---


async def _empty_fetch(ctx, *, limit):
    return SectionFetch(status="empty", total=0)


class _StubSource:
    def __init__(self, system, endpoint, fetch_fn):
        self.system = system
        self.endpoint = endpoint
        self._fetch = fetch_fn

    async def fetch(self, ctx, *, limit):
        return await self._fetch(ctx, limit=limit)


@pytest.fixture
def home_gateways(monkeypatch):
    """Injeta ports falsos no use case usado pela rota real do app.

    ``state`` mapeia seção → callable fetch; ``timeout``/``concurrency``
    configuráveis por teste.
    """
    state = {
        "tasks": _empty_fetch,
        "requests": _empty_fetch,
        "lmps": _empty_fetch,
        "timeout": 0.5,
        "concurrency": 3,
        "limit": 5,
        "contexts": [],  # ctxs recebidos pelos stubs, para asserção
    }

    def _builder():
        return GetEngineeringHome(
            tasks_source=_StubSource(
                "requests-api", "GET /requests/work-queue", _noop("tasks")
            ),
            requests_source=_StubSource(
                "requests-api", "GET /requests/mine", _noop("requests")
            ),
            lmps_source=_StubSource(
                "api-delpi", "GET /engineering/lmps", _noop("lmps")
            ),
            section_limit=state["limit"],
            source_timeout_seconds=state["timeout"],
            max_concurrent_sources=state["concurrency"],
        )

    def _noop(section):
        async def _fetch(ctx, *, limit):
            state["contexts"].append((section, ctx))
            return await state[section](ctx, limit=limit)

        return _fetch

    monkeypatch.setattr(
        home_routes_module, "build_get_engineering_home_use_case", _builder
    )
    return state


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _lmp_item(**over) -> HomeItem:
    data = {
        "id": "LMP-100",
        "kind": "lmp",
        "title": "Painel de transporte",
        "status": "in_progress",
        "status_label": "in_progress",
        "date": "2026-10-20",
        "href": "/apps/dashboard-lmps",
        "source": "api-delpi",
        "meta": {"sale_number": "LMP-100", "reference_revision": "3"},
    }
    data.update(over)
    return HomeItem(**data)


def _request_item(**over) -> HomeItem:
    data = {
        "id": "req-1",
        "kind": "request",
        "title": "000123",
        "status": "submitted",
        "status_label": "Em análise",
        "date": "2026-10-25T10:00:00Z",
        "href": "/apps/my-requests",
        "source": "requests-api",
        "meta": {"type_code": "raw-material-creation"},
    }
    data.update(over)
    return HomeItem(**data)


# --- AuthN ---


def test_home_requires_jwt(client):
    assert client.get("/v1/home").status_code == 401


def test_home_rejects_invalid_jwt(client, jwks_env):
    response = client.get("/v1/home", headers=_bearer("not-a-jwt"))
    assert response.status_code == 401


def test_home_rejects_wrong_signature(client, jwks_env):
    token = jwks_env["make_wrong_key_token"]()
    response = client.get("/v1/home", headers=_bearer(token))
    assert response.status_code == 401


# --- AuthZ Core ---


def test_home_without_engineering_access_denied(client, jwks_env, core_rbac):
    core_rbac["behavior"] = ("data", {"permissions": []})
    token = jwks_env["make_token"]()
    assert client.get("/v1/home", headers=_bearer(token)).status_code == 403


def test_home_sibling_permission_denied(client, jwks_env, core_rbac):
    core_rbac["behavior"] = ("data", {"permissions": [OTHER_PERMISSION]})
    token = jwks_env["make_token"]()
    assert client.get("/v1/home", headers=_bearer(token)).status_code == 403


def test_home_core_unavailable_fail_closed(client, jwks_env, core_rbac):
    core_rbac["behavior"] = ("raise", RuntimeError("core down"))
    token = jwks_env["make_token"]()
    assert client.get("/v1/home", headers=_bearer(token)).status_code == 503


def test_home_service_principal_denied(client, monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-1")
    headers = {}
    apply_internal_service_headers(headers)
    response = client.get("/v1/home", headers=headers)
    assert response.status_code == 403


def test_home_forged_claims_do_not_grant_access(client, jwks_env, core_rbac):
    # JWT alega superadmin; Core efetiva diz não — Core vence.
    core_rbac["behavior"] = ("data", {"permissions": [], "is_superadmin": False})
    token = jwks_env["make_token"](roles=["superadmin"])
    assert client.get("/v1/home", headers=_bearer(token)).status_code == 403


# --- Contrato e estados ---


def test_home_success_contract(
    client, jwks_env, core_rbac, home_gateways
):
    async def lmps_fetch(ctx, *, limit):
        return SectionFetch(status="available", items=(_lmp_item(),), total=7)

    async def requests_fetch(ctx, *, limit):
        return SectionFetch(
            status="available", items=(_request_item(),), total=2
        )

    home_gateways["lmps"] = lmps_fetch
    home_gateways["requests"] = requests_fetch
    core_rbac["behavior"] = (
        "data",
        {"permissions": [ENGINEERING_ACCESS], "id": "user-9"},
    )

    token = jwks_env["make_token"]()
    response = client.get("/v1/home", headers=_bearer(token))
    assert response.status_code == 200
    assert response.headers["x-operation-id"] == "get_engineering_home"
    assert response.headers.get("x-request-id")

    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_engineering_home"

    data = body["data"]
    assert data["schema_version"] == "1.0"
    assert data["status"] == "available"
    assert data["generated_at"].endswith("+00:00") or data[
        "generated_at"
    ].endswith("Z")

    sections = data["sections"]
    assert set(sections) == {
        "attention",
        "tasks",
        "lmps",
        "requests",
        "activity",
        "collaboration",
    }

    lmps = sections["lmps"]
    assert lmps["status"] == "available"
    assert lmps["total"] == 7
    assert lmps["source"] == {
        "system": "api-delpi",
        "endpoint": "GET /engineering/lmps",
    }
    item = lmps["items"][0]
    assert item["id"] == "LMP-100"
    assert item["kind"] == "lmp"
    assert item["source"] == "api-delpi"
    assert item["meta"]["reference_revision"] == "3"

    req = sections["requests"]
    assert req["status"] == "available"
    assert req["source"]["system"] == "requests-api"

    # Seções sem backend oficial — honestas, sem dados fabricados.
    assert sections["attention"]["status"] == "unavailable"
    assert sections["attention"]["reason"] == "no_official_source"
    assert sections["attention"]["items"] == []
    assert sections["activity"]["status"] == "unavailable"
    assert sections["collaboration"]["status"] == "not_implemented"
    assert sections["collaboration"]["items"] == []


def test_home_all_empty(client, jwks_env, core_rbac, home_gateways):
    token = jwks_env["make_token"]()
    response = client.get("/v1/home", headers=_bearer(token))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "available"
    assert data["sections"]["tasks"]["status"] == "empty"
    assert data["sections"]["tasks"]["items"] == []


def test_home_partial_failure_preserved(
    client, jwks_env, core_rbac, home_gateways
):
    async def lmps_fail(ctx, *, limit):
        return SectionFetch(status="unavailable", reason="upstream_error")

    async def tasks_ok(ctx, *, limit):
        return SectionFetch(
            status="available", items=(_request_item(kind="task"),), total=1
        )

    home_gateways["lmps"] = lmps_fail
    home_gateways["tasks"] = tasks_ok

    token = jwks_env["make_token"]()
    data = client.get("/v1/home", headers=_bearer(token)).json()["data"]
    assert data["status"] == "partial"
    assert data["sections"]["lmps"]["status"] == "unavailable"
    assert data["sections"]["lmps"]["reason"] == "upstream_error"
    assert data["sections"]["tasks"]["status"] == "available"


def test_home_all_sources_fail_global_unavailable(
    client, jwks_env, core_rbac, home_gateways
):
    async def fail(ctx, *, limit):
        return SectionFetch(status="unavailable", reason="transport_error")

    for section in ("tasks", "requests", "lmps"):
        home_gateways[section] = fail

    token = jwks_env["make_token"]()
    data = client.get("/v1/home", headers=_bearer(token)).json()["data"]
    assert data["status"] == "unavailable"
    for section in ("tasks", "requests", "lmps"):
        assert data["sections"][section]["status"] == "unavailable"


def test_home_forbidden_section_does_not_leak(
    client, jwks_env, core_rbac, home_gateways
):
    async def forbidden(ctx, *, limit):
        return SectionFetch(
            status="forbidden", message="Acesso negado pelo owner da fonte."
        )

    home_gateways["lmps"] = forbidden

    token = jwks_env["make_token"]()
    data = client.get("/v1/home", headers=_bearer(token)).json()["data"]
    assert data["status"] == "partial"
    section = data["sections"]["lmps"]
    assert section["status"] == "forbidden"
    assert section["items"] == []
    assert section["total"] is None


# --- Resiliência ---


def test_home_source_timeout_marked_unavailable(
    client, jwks_env, core_rbac, home_gateways
):
    async def slow(ctx, *, limit):
        await asyncio.sleep(0.3)
        return SectionFetch(status="available", items=(_lmp_item(),), total=1)

    home_gateways["lmps"] = slow
    home_gateways["timeout"] = 0.05

    token = jwks_env["make_token"]()
    data = client.get("/v1/home", headers=_bearer(token)).json()["data"]
    assert data["status"] == "partial"
    assert data["sections"]["lmps"]["status"] == "unavailable"
    assert data["sections"]["lmps"]["reason"] == "timeout"


def test_home_fanout_bounded(
    client, jwks_env, core_rbac, home_gateways
):
    in_flight = {"now": 0, "max": 0}

    def tracked(section):
        async def _fetch(ctx, *, limit):
            in_flight["now"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["now"])
            await asyncio.sleep(0.02)
            in_flight["now"] -= 1
            return SectionFetch(status="empty", total=0)

        return _fetch

    for section in ("tasks", "requests", "lmps"):
        home_gateways[section] = tracked(section)
    home_gateways["concurrency"] = 1

    token = jwks_env["make_token"]()
    response = client.get("/v1/home", headers=_bearer(token))
    assert response.status_code == 200
    assert in_flight["max"] == 1


def test_home_unexpected_source_error_marked_unavailable(
    client, jwks_env, core_rbac, home_gateways
):
    async def boom(ctx, *, limit):
        raise RuntimeError("unexpected")

    home_gateways["tasks"] = boom
    token = jwks_env["make_token"]()
    data = client.get("/v1/home", headers=_bearer(token)).json()["data"]
    assert data["sections"]["tasks"]["status"] == "unavailable"
    assert data["sections"]["tasks"]["reason"] == "upstream_error"
    assert data["status"] == "partial"


# --- Delegação e contexto ---


def test_home_delegates_user_context_to_sources(
    client, jwks_env, core_rbac, home_gateways
):
    core_rbac["behavior"] = (
        "data",
        {"permissions": [ENGINEERING_ACCESS], "id": "user-ctx-1"},
    )
    token = jwks_env["make_token"]()
    client.get(
        "/v1/home",
        headers={**_bearer(token), "X-Request-Id": "req-home-1"},
    )

    assert {section for section, _ in home_gateways["contexts"]} == {
        "tasks",
        "requests",
        "lmps",
    }
    for _section, ctx in home_gateways["contexts"]:
        assert ctx.user_id == "user-ctx-1"
        assert ctx.access_token == token  # delegação com JWT do usuário
        assert ctx.request_id == "req-home-1"  # correlação propagada


def test_home_users_isolated(client, jwks_env, core_rbac, home_gateways):
    async def requests_fetch(ctx, *, limit):
        return SectionFetch(
            status="available",
            items=(_request_item(id=f"req-of-{ctx.user_id}"),),
            total=1,
        )

    home_gateways["requests"] = requests_fetch

    core_rbac["behavior"] = ("data", {"permissions": [ENGINEERING_ACCESS]})
    core_rbac["behavior"][1]["id"] = "user-A"
    token_a = jwks_env["make_token"](sub="user-A")
    data_a = client.get("/v1/home", headers=_bearer(token_a)).json()["data"]

    core_rbac["behavior"][1]["id"] = "user-B"
    token_b = jwks_env["make_token"](sub="user-B")
    data_b = client.get("/v1/home", headers=_bearer(token_b)).json()["data"]

    assert (
        data_a["sections"]["requests"]["items"][0]["id"] == "req-of-user-A"
    )
    assert (
        data_b["sections"]["requests"]["items"][0]["id"] == "req-of-user-B"
    )


def test_home_openapi_contract(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    op = response.json()["paths"]["/v1/home"]["get"]
    assert op["operationId"] == "get_engineering_home"
