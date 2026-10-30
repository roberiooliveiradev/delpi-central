"""GET /closing/stock-kardex, /closing/inventory-adjustments and
/closing/cpv — BFF contract tests (R06/R07, doc 122, D-O1..D-O4).

Chain under test: middleware (JWT + RBAC snapshot) → principal_type/user
guard → ``controllership-finance.access`` → S2S gateway → typed errors.
The BFF never recalculates: filters forward verbatim, totals and parity
propagate untouched. Branch is a data filter only.
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
KARDEX = "/closing/stock-kardex"
INVENT = "/closing/inventory-adjustments"
CPV = "/closing/cpv"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "given_name": "Ana",
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


def test_kardex_requires_bearer(gateway):
    response = _client().get(f"{KARDEX}?{PERIOD}")
    assert response.status_code == 401
    gateway.get.assert_not_called()


def test_kardex_manage_only_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    assert _get(_client(), f"{KARDEX}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


def test_invent_requires_access(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert _get(_client(), f"{INVENT}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


def test_cpv_rbac_unavailable_fails_closed(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    assert _get(_client(), f"{CPV}?{PERIOD}").status_code == 503
    gateway.get.assert_not_called()


def test_service_principal_denied(monkeypatch, gateway):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    assert _get(_client(), f"{KARDEX}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


# --- routing / filter forwarding --------------------------------------------


def test_kardex_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(_client(), f"{KARDEX}?{PERIOD}&branch=02")
    assert response.status_code == 200
    assert gateway.get.call_args.args[0] == "/financeiro/stock-kardex"
    params = gateway.get.call_args.kwargs["params"]
    assert params["period"] == "2026-09"
    assert params["branch"] == "02"


def test_kardex_filters_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(),
        f"{KARDEX}?{PERIOD}&warehouse=01,99&product_code=P1"
        "&product_type=MP&movement_kind=entry&sort=product"
        "&sort_dir=desc&page=2&page_size=10",
    )
    assert response.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["warehouse"] == "01,99"
    assert params["product_code"] == "P1"
    assert params["product_type"] == "MP"
    assert params["movement_kind"] == "entry"
    assert params["sort"] == "product"
    assert params["sort_dir"] == "desc"
    assert params["page"] == 2
    assert params["page_size"] == 10


def test_kardex_summary_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {}}
    response = _get(_client(), f"{KARDEX}/summary?{PERIOD}")
    assert response.status_code == 200
    assert gateway.get.call_args.args[0] == "/financeiro/stock-kardex/summary"


def test_kardex_product_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {}}
    response = _get(
        _client(), f"{KARDEX}/products/10380012?{PERIOD}&branch=02"
    )
    assert response.status_code == 200
    assert (
        gateway.get.call_args.args[0]
        == "/financeiro/stock-kardex/products/10380012"
    )


def test_invent_routes_upstream_no_kind_param(gateway):
    """R07 never forwards document_kind — the producer owns the slice."""
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(), f"{INVENT}?{PERIOD}&branch=02&warehouse=01,99"
    )
    assert response.status_code == 200
    assert (
        gateway.get.call_args.args[0] == "/financeiro/inventory-adjustments"
    )
    params = gateway.get.call_args.kwargs["params"]
    assert "document_kind" not in params
    assert params["warehouse"] == "01,99"


def test_invent_summary_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {}}
    response = _get(_client(), f"{INVENT}/summary?{PERIOD}")
    assert response.status_code == 200
    assert (
        gateway.get.call_args.args[0]
        == "/financeiro/inventory-adjustments/summary"
    )


def test_cpv_routes_upstream(gateway):
    gateway.get.return_value = {"success": True, "data": {}}
    response = _get(_client(), f"{CPV}?{PERIOD}&branch=02&top_limit=5")
    assert response.status_code == 200
    assert gateway.get.call_args.args[0] == "/financeiro/cpv"
    params = gateway.get.call_args.kwargs["params"]
    assert params == {"period": "2026-09", "branch": "02", "top_limit": 5}


def test_invalid_branch_rejected(gateway):
    response = _get(_client(), f"{KARDEX}?{PERIOD}&branch=99")
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_invalid_movement_kind_rejected(gateway):
    response = _get(_client(), f"{KARDEX}?{PERIOD}&movement_kind=both")
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_delegated_bearer_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    _get(_client(), f"{KARDEX}?{PERIOD}")
    assert gateway.get.call_args.kwargs["access_token"] == TOKEN


# --- upstream error mapping --------------------------------------------------


def test_scope_unavailable_relays_typed_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(_client(), f"{KARDEX}?{PERIOD}")
    assert response.status_code == 403
    assert response.json()["data"]["error"]["code"] == "scope_unavailable"


def test_upstream_timeout_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    assert _get(_client(), f"{KARDEX}?{PERIOD}").status_code == 503


def test_upstream_500_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error", status_code=500
    )
    assert _get(_client(), f"{INVENT}?{PERIOD}").status_code == 503


def test_upstream_unexpected_body_maps_502(gateway):
    gateway.get.return_value = ["not", "an", "envelope"]
    assert _get(_client(), f"{CPV}?{PERIOD}").status_code == 502


# --- status propagation ------------------------------------------------------


def test_kardex_success_unwraps_data(gateway):
    payload = {
        "report": "stock-kardex",
        "period": "2026-09",
        "status": "available",
        "parityStatus": "PENDING",
        "totals": {"movementCount": 16178},
        "items": [{"productCode": "10380012"}],
    }
    gateway.get.return_value = {
        "success": True,
        "message": "Stock kardex loaded successfully.",
        "data": payload,
    }
    response = _get(_client(), f"{KARDEX}?{PERIOD}&branch=02")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == payload
    assert body["meta"]["operationId"] == "get_closing_stock_kardex"


def test_source_missing_status_propagates(gateway):
    payload = {
        "status": "source_missing",
        "branchesAvailable": [],
        "branchesMissing": ["02"],
        "items": [],
    }
    gateway.get.return_value = {"success": True, "data": payload}
    response = _get(_client(), f"{KARDEX}?period=1999-01&branch=02")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "source_missing"


def test_cpv_live_convention_propagates(gateway):
    payload = {
        "report": "cpv",
        "status": "available",
        "asOfConvention": "live",
        "summary": {"cpvTotal": "1804629.699000"},
    }
    gateway.get.return_value = {"success": True, "data": payload}
    response = _get(_client(), f"{CPV}?{PERIOD}&branch=02")
    assert response.status_code == 200
    assert response.json()["data"]["asOfConvention"] == "live"


# --- exports -----------------------------------------------------------------


def test_kardex_export_passthrough(gateway):
    gateway.get_bytes.return_value = (
        b"%PDF-fake",
        'attachment; filename="stock-kardex-2026-09-02.pdf"',
        "application/pdf",
    )
    response = _get(
        _client(), f"{KARDEX}/export?{PERIOD}&branch=02&format=pdf"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == b"%PDF-fake"
    assert (
        gateway.get_bytes.call_args.args[0]
        == "/financeiro/stock-kardex/export"
    )
    assert gateway.get_bytes.call_args.kwargs["params"]["format"] == "pdf"


def test_invent_export_passthrough(gateway):
    gateway.get_bytes.return_value = (
        b"col1;col2\na;b\n",
        'attachment; filename="inventory-adjustments-2026-09-02.csv"',
        "text/csv; charset=utf-8",
    )
    response = _get(
        _client(), f"{INVENT}/export?{PERIOD}&warehouse=01,99"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        gateway.get_bytes.call_args.args[0]
        == "/financeiro/inventory-adjustments/export"
    )


def test_export_invalid_format_rejected(gateway):
    response = _get(_client(), f"{KARDEX}/export?{PERIOD}&format=xlsx")
    assert response.status_code == 422
    gateway.get_bytes.assert_not_called()


# --- report matrix (R01–R15) -------------------------------------------------


@pytest.fixture
def checklist_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "reports_routes.ClosingChecklistRepository",
        lambda: fake,
    )
    return fake


def test_report_matrix_marks_r06_r07_operational(
    _auth_pipeline, checklist_repo
):
    """After real publication, R06/R07 are OPERATIONAL_VIEW/PENDING —
    never promoted to official parity."""
    checklist_repo.list_competence_items.return_value = []
    client = _client()
    response = client.get(
        "/closing/competences/2026-09/reports",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    reports = {
        r["report_id"]: r for r in response.json()["data"]["reports"]
    }
    assert reports["R06"]["source_kind"] == "OPERATIONAL_VIEW"
    assert reports["R06"]["operational_view"] == "stock-kardex"
    assert reports["R06"]["official_parity"] == "PENDING"
    assert reports["R07"]["source_kind"] == "OPERATIONAL_VIEW"
    assert reports["R07"]["operational_view"] == "inventory-adjustments"
    assert reports["R07"]["official_parity"] == "PENDING"
