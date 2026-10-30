"""GET /closing/cost-center-expenses (+/export) — BFF contract tests
(R10, doc 126, IMPLEMENTATION-STAGE-01) + CLARA semantic parity.

Chain under test: middleware (JWT + RBAC snapshot) → principal_type/user
guard → ``controllership-finance.access`` → S2S gateway → typed errors.
The BFF never recalculates: universe/view/filters forward verbatim,
totals and findings propagate untouched. Branch is a data filter only.

CLARA parity: ``read(report.cost_center_expenses)`` dispatches through
the semantic registry to the SAME route function the Portal calls —
``_call_route`` guarantees identical gate/envelope by construction.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    DelpiApiGatewayError,
)
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
PERIOD = "period=2026-09"
R10 = "/closing/cost-center-expenses"

CSV_BYTES = b"\xef\xbb\xbf# competencia=2026-09 universo=calculation\n"
CSV_CONTENT_TYPE = "text/csv; charset=utf-8"
DISPOSITION = 'attachment; filename="cost-center-expenses-2026-09-all-calculation.csv"'


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}

    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: False
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def gateway(monkeypatch):
    fake = MagicMock()
    fake.get_bytes.return_value = (
        CSV_BYTES,
        DISPOSITION,
        CSV_CONTENT_TYPE,
    )
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes.closing_routes."
        "ApiDelpiSettlementsGateway",
        lambda *a, **k: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _get(client, path, token: str = TOKEN):
    return client.get(path, headers={"Authorization": f"Bearer {token}"})


# --- authorization ----------------------------------------------------------


def test_r10_requires_bearer(gateway):
    response = _client().get(f"{R10}?{PERIOD}")
    assert response.status_code == 401
    gateway.get.assert_not_called()


def test_r10_manage_only_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    assert _get(_client(), f"{R10}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


def test_r10_requires_access(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert _get(_client(), f"{R10}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


def test_r10_rbac_unavailable_fails_closed(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    assert _get(_client(), f"{R10}?{PERIOD}").status_code == 503
    gateway.get.assert_not_called()


def test_r10_service_principal_denied(monkeypatch, gateway):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    assert _get(_client(), f"{R10}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


# --- routing / filter forwarding --------------------------------------------


def test_r10_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(_client(), f"{R10}?{PERIOD}&branch=02")
    assert response.status_code == 200
    assert (
        gateway.get.call_args.args[0]
        == "/financeiro/cost-center-expenses"
    )
    params = gateway.get.call_args.kwargs["params"]
    assert params["period"] == "2026-09"
    assert params["branch"] == "02"
    assert params["universe"] == "calculation"


def test_r10_universe_view_and_filters_forwarded(gateway):
    """Universe/view are contract params — the BFF forwards them
    verbatim; it never recalculates or mixes universes."""
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(),
        f"{R10}?{PERIOD}&universe=investigation&view=divergences"
        "&cost_center=0401&product_code=P1&document=000123"
        "&supplier_code=F001&tes=101&sort=cost_center&sort_dir=desc"
        "&page=2&page_size=10",
    )
    assert response.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["universe"] == "investigation"
    assert params["view"] == "divergences"
    assert params["cost_center"] == "0401"
    assert params["product_code"] == "P1"
    assert params["document"] == "000123"
    assert params["supplier_code"] == "F001"
    assert params["tes"] == "101"
    assert params["sort"] == "cost_center"
    assert params["sort_dir"] == "desc"
    assert params["page"] == 2
    assert params["page_size"] == 10


def test_r10_invalid_universe_rejected(gateway):
    response = _get(_client(), f"{R10}?{PERIOD}&universe=combined")
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_r10_invalid_branch_rejected(gateway):
    response = _get(_client(), f"{R10}?{PERIOD}&branch=99")
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_r10_delegated_bearer_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    _get(_client(), f"{R10}?{PERIOD}")
    assert gateway.get.call_args.kwargs["access_token"] == TOKEN


# --- upstream error mapping --------------------------------------------------


def test_r10_scope_unavailable_relays_typed_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(_client(), f"{R10}?{PERIOD}")
    assert response.status_code == 403
    assert response.json()["data"]["error"]["code"] == "scope_unavailable"


def test_r10_upstream_timeout_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    assert _get(_client(), f"{R10}?{PERIOD}").status_code == 503


# --- export passthrough -------------------------------------------------------


def test_r10_export_streams_bytes(gateway):
    response = _get(
        _client(),
        f"{R10}/export?{PERIOD}&format=csv&universe=investigation",
    )
    assert response.status_code == 200
    assert response.content == CSV_BYTES
    assert response.headers["content-type"].startswith("text/csv")
    assert DISPOSITION in response.headers["content-disposition"]
    args = gateway.get_bytes.call_args
    assert args.args[0] == "/financeiro/cost-center-expenses/export"
    assert args.kwargs["params"]["universe"] == "investigation"
    assert args.kwargs["params"]["format"] == "csv"


def test_r10_export_requires_access(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert (
        _get(_client(), f"{R10}/export?{PERIOD}").status_code == 403
    )
    gateway.get_bytes.assert_not_called()


# --- CLARA semantic parity ----------------------------------------------------


def test_clara_read_action_registered():
    """read(report.cost_center_expenses) is a first-class semantic
    action — never a flat MCP tool."""
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )

    spec = sb.READ_ACTIONS.get(("report", "cost_center_expenses"))
    assert spec is not None
    assert "period" in spec["required"]
    allowed = set(spec["allowed"])
    assert {
        "branch",
        "universe",
        "view",
        "cost_center",
        "product_code",
        "document",
        "supplier_code",
        "tes",
        "page",
        "page_size",
    } <= allowed


def test_clara_dispatch_reaches_same_portal_route(monkeypatch):
    """The bridge handler calls ``_call_route`` with the very function
    the Portal route uses — parity by construction."""
    from controllership_finance_app.interface.http.routes import (
        closing_routes,
    )
    from controllership_finance_app.interface.mcp import tool_bridge

    seen = {}
    monkeypatch.setattr(
        tool_bridge,
        "_user_and_access",
        lambda: (MagicMock(), SimpleNamespace(id="u-1")),
    )

    def fake_call_route(fn, request, **params):
        seen["fn"] = fn
        seen["params"] = params
        return tool_bridge._ok({"items": []})

    monkeypatch.setattr(tool_bridge, "_call_route", fake_call_route)
    result = tool_bridge.tool_get_cost_center_expenses(
        period="2026-09",
        branch="01",
        universe="investigation",
        view="divergences",
        cost_center="0401",
        tes="101",
    )
    assert result.is_error is False
    assert seen["fn"] is closing_routes.get_closing_cost_center_expenses
    assert seen["params"]["universe"] == "investigation"
    assert seen["params"]["view"] == "divergences"
    assert seen["params"]["cost_center"] == "0401"
    assert seen["params"]["tes"] == "101"
    assert seen["params"]["include_findings"] is True


def test_clara_semantic_dispatch_forwards_allowed_params(monkeypatch):
    """read(report.cost_center_expenses) via the semantic dispatcher —
    not just the Python function."""
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )
    from controllership_finance_app.interface.mcp import tool_bridge

    seen = {}

    def fake(**kw):
        seen.update(kw)
        return tool_bridge._ok({"items": []})

    user = SimpleNamespace(
        id="u-1", is_superadmin=False, name="T", email="t@d"
    )
    monkeypatch.setattr(
        sb, "_user_and_access", lambda: (MagicMock(), user)
    )
    monkeypatch.setattr(sb, "actor_subject", lambda _u: "sub-1")
    monkeypatch.setitem(
        sb.READ_ACTIONS,
        ("report", "cost_center_expenses"),
        {
            "handler": fake,
            "ref_param": None,
            "required": ("period",),
            "allowed": ("universe", "view", "cost_center"),
        },
    )
    res = sb.tool_read(
        entity="report",
        action="cost_center_expenses",
        period="2026-09",
        filters={"universe": "investigation", "cost_center": "0401"},
    )
    assert res.is_error is False
    assert seen["universe"] == "investigation"
    assert seen["cost_center"] == "0401"


def test_clara_semantic_dispatch_rejects_unknown_param():
    from controllership_finance_app.interface.mcp import (
        semantic_bridge as sb,
    )

    res = sb.tool_read(
        entity="report",
        action="cost_center_expenses",
        period="2026-09",
        filters={"raw_sql": "SELECT *"},
    )
    assert res.is_error is True
