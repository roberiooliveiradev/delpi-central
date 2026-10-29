"""G3 — contrato, AuthN/AuthZ unificada e resiliência das rotas LMP.

Cobre (G3.5/G3.9): `engineering.access` exclusivo; manage sem access não
ganha acesso operacional; permissão legada não substitui; 401 sem JWT;
fail-closed com Core indisponível; principal humano exigido; estados
honestos (unavailable/forbidden); validação de período; envelope.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

import engineering_app.interface.http.routes.lmp_routes as lmp_routes
from engineering_app.application.models.lmp import LmpFact, LmpFactsResult
from engineering_app.main import app

ENGINEERING_ACCESS = "engineering.access"
ENGINEERING_MANAGE = "engineering.manage"
LEGACY_PERMISSION = "dashboard-lmps.view"


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fact(**over):
    base = dict(
        branch="01",
        sale_number="OV900",
        sale_description="Fato",
        listing_kind_source="LMP",
        listing_kind="LMP",
        has_sample_anchor=False,
        has_lmp_finalized=True,
        sample_eng_minutes=0,
        residence_minutes=120,
        start_date="20260501",
        end_date="20260507",
        homolog_revision="001",
        measurement_revision="001",
        homolog_date="20260501",
        cycle_index=1,
        engineering_status="FINALIZADA",
        qtd_engineering_entries=1,
        qtd_engineering_closed=1,
        qtd_advanced_from_engineering=0,
        qtd_returned_from_engineering=0,
        qtd_pi=5,
    )
    base.update(over)
    return LmpFact.from_dict(base)


class _StubFacts:
    def __init__(self, page: LmpFactsResult):
        self._page = page
        self.calls: list[dict] = []
        self.fact_detail = None
        self.history = None

    async def fetch_facts(self, ctx, **params):
        self.calls.append(params)
        return self._page

    async def fetch_pi_counts(self, ctx, *, ov_keys, branch):
        from engineering_app.application.models.lmp import LmpPiCountsResult

        return LmpPiCountsResult(
            status="available",
            counts=((("01", "OV900", "001"), 5),),
        )

    async def fetch_fact(self, ctx, **params):
        self.calls.append(params)
        if self.fact_detail is not None:
            return self.fact_detail
        from engineering_app.application.models.lmp import LmpFactDetailResult

        return LmpFactDetailResult(
            status="available",
            fact={
                "branch": "01",
                "sale_number": "OV900",
                "sale_description": "Fato",
                "listing_kind": "LMP",
                "start_date": "2026-05-01",
                "end_date": "2026-05-07",
                "engineering_status": "FINALIZADA",
                "engineering_total_minutes": 120,
                "qtd_pi": 5,
                "list_products": [{"code": "P1"}],
            },
            provenance={"source_system": "TOTVS"},
        )

    async def fetch_history(self, ctx, **params):
        self.calls.append(params)
        if self.history is not None:
            return self.history
        from engineering_app.application.models.lmp import LmpHistoryResult

        return LmpHistoryResult(
            status="available",
            items=(
                {
                    "revision": "001",
                    "process_code": "ENG",
                    "stage_code": "10",
                    "start_date": "2026-05-01",
                    "start_time": "08:00",
                    "end_date": "2026-05-02",
                    "end_time": "10:00",
                    "limit_date": "2026-05-05",
                    "status_code": "F",
                },
            ),
            branch="01",
            reference_revision="001",
            panel_start_date="2026-05-01",
            provenance={"source_system": "TOTVS"},
        )


def _available_page(facts=()):
    return LmpFactsResult(
        status="available",
        facts=tuple(facts),
        total=len(facts),
        provenance={"source_system": "TOTVS", "integration_owner": "api-delpi"},
        policy={"period_policy": "work_month_lmp"},
    )


def _install_stub(monkeypatch, page: LmpFactsResult):
    stub = _StubFacts(page)

    class _UseCase:
        def __init__(self):
            self._facts = stub

        async def execute(self, ctx, query):
            from engineering_app.application.use_cases.list_lmps_dashboard import (
                ListLmpsDashboardUseCase,
            )
            return await ListLmpsDashboardUseCase(stub).execute(ctx, query)

    monkeypatch.setattr(
        lmp_routes, "build_list_lmps_dashboard_use_case", _UseCase
    )
    return stub


def _install_summary_stub(monkeypatch, page: LmpFactsResult):
    stub = _StubFacts(page)

    class _UseCase:
        def __init__(self):
            self._facts = stub

        async def execute(self, ctx, query):
            from engineering_app.application.use_cases.get_lmp_summary import (
                GetLmpSummaryUseCase,
            )
            return await GetLmpSummaryUseCase(stub).execute(ctx, query)

    monkeypatch.setattr(
        lmp_routes, "build_get_lmp_summary_use_case", _UseCase
    )
    return stub


def _install_detail_history_stubs(monkeypatch, page: LmpFactsResult):
    stub = _StubFacts(page)

    class _DetailUseCase:
        def __init__(self):
            self._facts = stub

        async def execute(self, ctx, query):
            from engineering_app.application.use_cases.get_lmp_detail import (
                GetLmpDetailUseCase,
            )
            return await GetLmpDetailUseCase(stub).execute(ctx, query)

    class _HistoryUseCase:
        def __init__(self, view):
            self._facts = stub
            self._view = view

        async def execute(self, ctx, query):
            from engineering_app.application.use_cases.get_lmp_history import (
                GetLmpHistoryUseCase,
            )
            return await GetLmpHistoryUseCase(stub, view=self._view).execute(
                ctx, query
            )

    monkeypatch.setattr(
        lmp_routes, "build_get_lmp_detail_use_case", lambda: _DetailUseCase()
    )
    monkeypatch.setattr(
        lmp_routes,
        "build_get_lmp_history_use_case",
        lambda *, view: _HistoryUseCase(view),
    )
    return stub


# --- AuthN / AuthZ unificada -----------------------------------------------


def test_list_lmps_requires_auth(client):
    resp = client.get("/v1/lmps")
    assert resp.status_code == 401


def test_summary_requires_auth(client):
    resp = client.get("/v1/lmps/summary")
    assert resp.status_code == 401


def test_list_lmps_denied_without_engineering_access(
    client, jwks_env, core_rbac
):
    core_rbac["behavior"] = ("data", rbac_payload_local([]))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    assert resp.status_code == 403


def test_manage_alone_does_not_grant_operational_access(
    client, jwks_env, core_rbac
):
    # G3.5 — sem hierarquia implícita entre manage e access.
    core_rbac["behavior"] = ("data", rbac_payload_local([ENGINEERING_MANAGE]))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    assert resp.status_code == 403


def test_legacy_permission_does_not_grant_access(
    client, jwks_env, core_rbac
):
    # G3.9 — `dashboard-lmps.view` nunca substitui `engineering.access`.
    core_rbac["behavior"] = ("data", rbac_payload_local([LEGACY_PERMISSION]))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    assert resp.status_code == 403


def test_access_with_both_permissions_allowed(
    client, jwks_env, core_rbac, monkeypatch
):
    core_rbac["behavior"] = (
        "data",
        rbac_payload_local([ENGINEERING_ACCESS, ENGINEERING_MANAGE]),
    )
    _install_stub(monkeypatch, _available_page([_fact()]))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "list_lmps"
    item = body["data"]["items"][0]
    assert item["status"] == "Pontual"
    assert body["data"]["provenance"]["source_system"] == "TOTVS"


def test_core_unavailable_fails_closed(client, jwks_env, core_rbac):
    # Fail-closed: Core /me indisponível → nenhum acesso concedido.
    core_rbac["behavior"] = ("raise", RuntimeError("core unreachable"))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    # Deny emitido pelo boundary delpi_auth (envelope {"detail": ...}).
    assert resp.status_code in (403, 503)


# --- Parâmetros e estados honestos -----------------------------------------


def test_invalid_period_returns_400(client, jwks_env, core_rbac, monkeypatch):
    _install_stub(monkeypatch, _available_page([_fact()]))
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/lmps?start_date=2026-06-01&end_date=2026-05-01",
        headers=_bearer(token),
    )
    assert resp.status_code == 400


def test_unavailable_source_is_honest(
    client, jwks_env, core_rbac, monkeypatch
):
    page = LmpFactsResult(
        status="unavailable",
        facts=(),
        total=None,
        reason="timeout",
    )
    _install_stub(monkeypatch, page)
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    body = resp.json()
    assert body["data"]["status"] == "unavailable"
    assert body["data"]["items"] == []


def test_forbidden_source_maps_403(client, jwks_env, core_rbac, monkeypatch):
    page = LmpFactsResult(
        status="forbidden",
        facts=(),
        total=None,
        reason="s2s_denied",
    )
    _install_stub(monkeypatch, page)
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps", headers=_bearer(token))
    assert resp.status_code == 403


def test_summary_total_items_counts_all_listing_kinds(
    client, jwks_env, core_rbac, monkeypatch
):
    """G4.B divergência real: legado `total_items` = universo filtrado
    (todos os kinds), não apenas LMPs. Regressão de paridade do
    `lmp_only=True` removido do fetch de facts do summary."""
    facts = [
        _fact(sale_number="OV901"),  # LMP
        _fact(
            sale_number="OV902",
            listing_kind_source="AMOSTRA",
            listing_kind="AMOSTRA",
            has_sample_anchor=True,
            has_lmp_finalized=False,
            engineering_status="EM_ANDAMENTO",
            sample_eng_minutes=45,
        ),
        _fact(
            sale_number="OV903",
            listing_kind_source="OUTRO",
            listing_kind="OUTRO",
            has_lmp_finalized=False,
            engineering_status="EM_ANDAMENTO",
        ),
    ]
    stub = _install_summary_stub(monkeypatch, _available_page(facts))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps/summary", headers=_bearer(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    # facts fetch NÃO pode ser estreitado a LMP — semântica legada.
    assert stub.calls[0].get("listing_type") is None
    assert data["total_items"] == 3
    assert data["total_lmps"] == 1


# --- E-LMP-02/04/05 — detalhe e histórico (G4.C) ---------------------------


def test_detail_requires_auth(client):
    resp = client.get("/v1/lmps/OV900")
    assert resp.status_code == 401


def test_history_events_requires_auth(client):
    resp = client.get("/v1/lmps/OV900/history/events")
    assert resp.status_code == 401


def test_history_flow_requires_auth(client):
    resp = client.get("/v1/lmps/OV900/history/flow")
    assert resp.status_code == 401


def test_detail_returns_enriched_item(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_detail_history_stubs(monkeypatch, _available_page())
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps/OV900", headers=_bearer(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "available"
    item = data["item"]
    # campos calculados pelo domínio migrado (R01–R05)
    assert item["nivel"] == "Nível 1"
    assert item["status"] == "Pontual"
    assert item["data_limite"] == "2026-05-07"
    assert item["list_products"] == [{"code": "P1"}]
    assert item["list_history"] == []
    assert data["provenance"]["source_system"] == "TOTVS"


def test_detail_not_found_returns_404(
    client, jwks_env, core_rbac, monkeypatch
):
    from engineering_app.application.models.lmp import LmpFactDetailResult

    stub = _install_detail_history_stubs(monkeypatch, _available_page())
    stub.fact_detail = LmpFactDetailResult(
        status="not_found", reason="lmp_not_found"
    )
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps/OV999", headers=_bearer(token))
    assert resp.status_code == 404


def test_detail_denied_without_engineering_access(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_detail_history_stubs(monkeypatch, _available_page())
    core_rbac["behavior"] = ("data", rbac_payload_local([]))
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps/OV900", headers=_bearer(token))
    assert resp.status_code == 403


def test_history_events_enriched(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_detail_history_stubs(monkeypatch, _available_page())
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/lmps/OV900/history/events", headers=_bearer(token)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["view"] == "events"
    assert data["total"] == 1
    assert data["reference_revision"] == "001"
    event = data["items"][0]
    assert event["process_label"]
    assert event["stage_label"]


def test_history_flow_enriched(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_detail_history_stubs(monkeypatch, _available_page())
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/lmps/OV900/history/flow", headers=_bearer(token)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["view"] == "flow"
    event = data["items"][0]
    assert event["process_label"]
    assert event["stage_label"]


def test_detail_unavailable_source_is_honest(
    client, jwks_env, core_rbac, monkeypatch
):
    from engineering_app.application.models.lmp import LmpFactDetailResult

    stub = _install_detail_history_stubs(monkeypatch, _available_page())
    stub.fact_detail = LmpFactDetailResult(
        status="unavailable", reason="timeout"
    )
    token = jwks_env["make_token"]()
    resp = client.get("/v1/lmps/OV900", headers=_bearer(token))
    assert resp.json()["data"]["status"] == "unavailable"


def test_invalid_listing_type_returns_400(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available_page())
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/lmps?listing_type=ZZZ", headers=_bearer(token)
    )
    assert resp.status_code == 400


def rbac_payload_local(permissions, **overrides) -> dict:
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "roles": [],
        "groups": [],
        "permissions": list(permissions),
        "is_superadmin": False,
    }
    data.update(overrides)
    return data
