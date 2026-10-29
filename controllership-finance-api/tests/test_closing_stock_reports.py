"""R05/R08 proxy routes + analytical reconciliation — BFF tests.

The proxies add only the ``controllership-finance.access`` gate and
typed-error relay; serialization and calculations stay at api-delpi.
The analytical route composes the three operational datasets and never
touches the governed P3 projection.
"""

from __future__ import annotations

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
DRE = "controllership-finance.access.dre"
TOKEN = "viewer-test-token"
PERIOD = "period=2026-09"

PDF_BYTES = b"%PDF-1.4 fake"
PDF_CONTENT_TYPE = "application/pdf"
CSV_BYTES = b"\xef\xbb\xbf# r05\n"
CSV_CONTENT_TYPE = "text/csv; charset=utf-8"


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
        'attachment; filename="report.csv"',
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


def _envelope(data) -> dict:
    return {"success": True, "message": "OK", "data": data, "meta": {}}


# --- R05 proxy ----------------------------------------------------------------


def test_stock_movements_requires_bearer(gateway):
    assert (
        _client().get(f"/closing/stock-movements?{PERIOD}").status_code
        == 401
    )
    gateway.get.assert_not_called()


def test_stock_movements_dre_only_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[DRE])
    assert (
        _get(_client(), f"/closing/stock-movements?{PERIOD}").status_code
        == 403
    )
    gateway.get.assert_not_called()


def test_stock_movements_forwards_filters(gateway):
    gateway.get.return_value = _envelope({"report": "stock-movements"})
    response = _get(
        _client(),
        f"/closing/stock-movements?{PERIOD}&branch=01"
        "&report_scope=mp_pi_pa",
    )
    assert response.status_code == 200
    call = gateway.get.call_args
    assert call.args[0] == "/financeiro/stock-movements"
    assert call.kwargs["params"] == {
        "period": "2026-09",
        "branch": "01",
        "report_scope": "mp_pi_pa",
    }


def test_stock_movements_scope_unavailable_relays_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(_client(), f"/closing/stock-movements?{PERIOD}")
    assert response.status_code == 403
    assert (
        response.json()["data"]["error"]["code"] == "scope_unavailable"
    )


def test_stock_movements_export_pdf_passthrough(gateway):
    gateway.get_bytes.return_value = (
        PDF_BYTES,
        'attachment; filename="r05.pdf"',
        PDF_CONTENT_TYPE,
    )
    response = _get(
        _client(),
        f"/closing/stock-movements/export?{PERIOD}&format=pdf",
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == PDF_BYTES
    call = gateway.get_bytes.call_args
    assert call.args[0] == "/financeiro/stock-movements/export"
    assert call.kwargs["params"]["format"] == "pdf"


def test_stock_movements_export_not_exportable_relays_409(gateway):
    gateway.get_bytes.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=409,
        error_code="not_exportable",
    )
    response = _get(
        _client(), f"/closing/stock-movements/export?{PERIOD}"
    )
    assert response.status_code == 409
    assert response.json()["data"]["error"]["code"] == "not_exportable"


# --- R08 proxy ----------------------------------------------------------------


def test_work_in_process_requires_bearer(gateway):
    assert (
        _client().get(f"/closing/work-in-process?{PERIOD}").status_code
        == 401
    )
    gateway.get.assert_not_called()


def test_work_in_process_forwards_pagination_and_warehouse(gateway):
    gateway.get.return_value = _envelope({"report": "work-in-process"})
    response = _get(
        _client(),
        f"/closing/work-in-process?{PERIOD}&branch=02&warehouse=99"
        "&page=2&page_size=25",
    )
    assert response.status_code == 200
    call = gateway.get.call_args
    assert call.args[0] == "/financeiro/work-in-process"
    params = call.kwargs["params"]
    assert params["branch"] == "02"
    assert params["warehouse"] == "99"
    assert params["page"] == 2
    assert params["page_size"] == 25


def test_work_in_process_export_passthrough(gateway):
    response = _get(
        _client(), f"/closing/work-in-process/export?{PERIOD}"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    call = gateway.get_bytes.call_args
    assert call.args[0] == "/financeiro/work-in-process/export"
    assert call.kwargs["params"]["format"] == "csv"


def test_work_in_process_export_rejects_bad_format(gateway):
    assert (
        _get(
            _client(),
            f"/closing/work-in-process/export?{PERIOD}&format=xlsx",
        ).status_code
        == 422
    )
    gateway.get_bytes.assert_not_called()


# --- analytical reconciliation -------------------------------------------------

ROUTE_REC = "/closing/analytics/stock-reconciliation"


def _movements_payload(closing="14469584.010000", status="available"):
    return {
        "report": "stock-movements",
        "status": status,
        "dataAsOf": "2026-09-30",
        "parityStatus": "PENDING",
        "totals": {
            "openingBalance": "14000000.000000",
            "closingBalance": closing,
            "netMovement": "469584.010000",
        },
        "provenance": {"engine": "minha-delpi-r05-movements-engine"},
    }


def _inventory_payload(stock="13767296.141000", status="available"):
    return {
        "report": "stock-inventory",
        "status": status,
        "dataAsOf": "2026-09-30",
        "parityStatus": "PENDING",
        "stockTotal": stock,
        "processPhysicalTotal": "702287.869000",
        "processAllocatedTotal": "169128.463000",
        "processTotal": "871416.332000",
        "grandTotal": "14638712.473000",
        "historicalTotal": "14469584.010000",
        "provenance": {"engine": "minha-delpi-p7-engine"},
    }


def _wip_payload(physical="702287.869000", status="available"):
    return {
        "report": "work-in-process",
        "status": status,
        "dataAsOf": "2026-09-30",
        "parityStatus": "PENDING",
        "physicalTotal": physical,
        "allocatedTotal": "169128.463000",
        "grandTotal": "871416.332000",
        "provenance": {"engine": "minha-delpi-wip-engine"},
    }


def _wire_analytics(gateway, *, mov=None, inv=None, wip=None):
    responses = {
        "/financeiro/stock-movements": _envelope(
            mov if mov is not None else _movements_payload()
        ),
        "/financeiro/stock-inventory": _envelope(
            inv if inv is not None else _inventory_payload()
        ),
        "/financeiro/work-in-process": _envelope(
            wip if wip is not None else _wip_payload()
        ),
    }

    def _get_route(path, *, access_token, params):
        if isinstance(responses.get(path), Exception):
            raise responses[path]
        return responses.get(path)

    gateway.get.side_effect = _get_route


def test_reconciliation_requires_bearer(gateway):
    assert _client().get(f"{ROUTE_REC}?{PERIOD}").status_code == 401
    gateway.get.assert_not_called()


def test_reconciliation_dre_only_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[DRE])
    assert _get(_client(), f"{ROUTE_REC}?{PERIOD}").status_code == 403
    gateway.get.assert_not_called()


def test_reconciliation_exact_parity(gateway):
    """positive — SA = EM ESTOQUE + loc99 → divergence R$ 0,00."""
    _wire_analytics(gateway)
    response = _get(_client(), f"{ROUTE_REC}?{PERIOD}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["eligibility"] == "ELIGIBLE"
    assert data["parity"] == "EXACT_PARITY"
    assert data["divergenceCents"] == "0.00"
    assert data["operands"]["entradasSaidas"]["value"] == (
        "14469584.010000"
    )
    assert data["operands"]["p7"]["value"] == "13767296.141000"
    assert data["operands"]["h02"]["value"] == "702287.869000"
    assert data["kind"] == "analytical"
    assert data["governedReconciliation"] == "not_persisted"


def test_reconciliation_divergence_positive_cent(gateway):
    """negative — one cent of divergence stays divergence."""
    _wire_analytics(
        gateway, mov=_movements_payload(closing="14469584.020000")
    )
    data = _get(_client(), f"{ROUTE_REC}?{PERIOD}").json()["data"]
    assert data["parity"] == "DIVERGENCE"
    assert data["divergenceCents"] == "0.01"


def test_reconciliation_divergence_large(gateway):
    """sibling — historical-style residual is reported, not clamped."""
    _wire_analytics(
        gateway, mov=_movements_payload(closing="14518244.790000")
    )
    data = _get(_client(), f"{ROUTE_REC}?{PERIOD}").json()["data"]
    assert data["parity"] == "DIVERGENCE"
    assert data["divergenceCents"] == "48660.78"


def test_reconciliation_missing_source_never_zero(gateway):
    """source_missing on one operand → INELIGIBLE, no computed zero."""
    _wire_analytics(
        gateway, mov=_movements_payload(status="source_missing")
    )
    data = _get(_client(), f"{ROUTE_REC}?{PERIOD}").json()["data"]
    assert data["eligibility"] == "INELIGIBLE"
    assert data["ineligibleOperands"] == ["entradasSaidas"]
    assert data["divergence"] is None
    assert data["divergenceCents"] is None
    assert data["parity"] == "NOT_COMPUTED"


def test_reconciliation_incomplete_source_ineligible(gateway):
    """INCOMPLETE (partial branch coverage) never reconciles."""
    _wire_analytics(
        gateway, inv=_inventory_payload(status="incomplete")
    )
    data = _get(_client(), f"{ROUTE_REC}?{PERIOD}").json()["data"]
    assert data["eligibility"] == "INELIGIBLE"
    assert data["ineligibleOperands"] == ["p7"]
    assert data["parity"] == "NOT_COMPUTED"


def test_reconciliation_upstream_failure_marks_operand(gateway):
    """A 5xx/timeout on one source degrades to an explicit unavailable
    operand — the route still answers so the analyst sees what failed."""
    _wire_analytics(gateway)
    responses_error = DelpiApiGatewayError("api-delpi timeout")

    def _get_route(path, *, access_token, params):
        if path == "/financeiro/work-in-process":
            raise responses_error
        return _envelope(
            _movements_payload()
            if path == "/financeiro/stock-movements"
            else _inventory_payload()
        )

    gateway.get.side_effect = _get_route
    response = _get(_client(), f"{ROUTE_REC}?{PERIOD}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["eligibility"] == "INELIGIBLE"
    assert data["ineligibleOperands"] == ["h02"]
    assert data["operands"]["h02"]["status"] == "UNAVAILABLE"
    assert data["parity"] == "NOT_COMPUTED"


def test_reconciliation_scope_unavailable_relays_403(gateway):
    _wire_analytics(gateway)
    err = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    gateway.get.side_effect = err
    response = _get(_client(), f"{ROUTE_REC}?{PERIOD}")
    assert response.status_code == 403
    assert (
        response.json()["data"]["error"]["code"] == "scope_unavailable"
    )


def test_reconciliation_same_period_forwarded_to_all(gateway):
    """Same period/branch/scope reach every operand — no mixed
    references."""
    _wire_analytics(gateway)
    _get(
        _client(),
        f"{ROUTE_REC}?{PERIOD}&branch=01&report_scope=mp_pi_pa",
    )
    calls = {
        c.args[0]: c.kwargs["params"] for c in gateway.get.call_args_list
    }
    for path in _ANALYTICS_PATHS:
        params = calls[path]
        assert params["period"] == "2026-09"
        assert params["branch"] == "01"
        assert params["report_scope"] == "mp_pi_pa"


_ANALYTICS_PATHS = (
    "/financeiro/stock-movements",
    "/financeiro/stock-inventory",
    "/financeiro/work-in-process",
)
