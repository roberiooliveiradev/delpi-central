"""HTTP contract for /financeiro/settlements/* — S2S + delegated user + scope."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from delpi_auth.service_errors import (
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
)
from delpi_auth.service_identity import ServiceIdentity

VALID_IDENTITY = ServiceIdentity(
    client_id="controllership-finance-api",
    subject="service-account-cf",
    scopes=frozenset({"settlements.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)

S2S_HEADERS = {
    "X-Delpi-Service-Authorization": "Bearer service-jwt",
    "X-Delpi-Caller-App": "controllership-finance-api",
    "Authorization": "Bearer user-jwt",
}

PERIOD = "start_date=2026-01-01&end_date=2026-01-31"


@pytest.fixture
def settlements_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.settlements_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _request_headers(headers):
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(identity=VALID_IDENTITY, error=None):
    validator = MagicMock()
    if error is not None:
        validator.validate.side_effect = error
    else:
        validator.validate.return_value = identity
    return validator


def _patch_s2s(monkeypatch, request, validator=None):
    monkeypatch.setattr(
        "app.interface.http.s2s_service_access.get_request",
        lambda: request,
    )
    if validator is not None:
        monkeypatch.setattr(
            "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
            classmethod(lambda cls: validator),
        )


def _patch_user(monkeypatch, principal_type="user"):
    user = SimpleNamespace(
        id="user-1",
        email="user@delpi.local",
        principal_type=principal_type,
    )
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.settlements_route_helpers."
        "resolve_user_context",
        lambda: user,
    )


def test_router_exposes_three_routes() -> None:
    from app.interface.http.routes.financeiro.settlements_router import router

    assert router.prefix == "/financeiro/settlements"
    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert paths == {
        "/financeiro/settlements/payables",
        "/financeiro/settlements/receivables",
        "/financeiro/settlements/summary",
    }


def test_missing_service_header_returns_401(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = settlements_client.get(
        f"/financeiro/settlements/payables?{PERIOD}", headers=S2S_HEADERS
    )
    # header intentionally absent in the fake request — strict S2S rejects
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = settlements_client.get(
        f"/financeiro/settlements/payables?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 401


def test_wrong_client_returns_403(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = settlements_client.get(
        f"/financeiro/settlements/payables?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("settlements.read")),
    )
    response = settlements_client.get(
        f"/financeiro/settlements/receivables?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_unresolved_scope_returns_typed_403(
    settlements_client: TestClient, monkeypatch
) -> None:
    """Default resolver is fail-closed (D3.1): valid S2S + delegated user
    still gets `scope_unavailable`, never real rows."""
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(),
    )
    _patch_user(monkeypatch)
    for path in ("payables", "receivables", "summary"):
        response = settlements_client.get(
            f"/financeiro/settlements/{path}?{PERIOD}", headers=S2S_HEADERS
        )
        assert response.status_code == 403, path
        body = response.json()
        assert body.get("success") is False
        assert body.get("error", {}).get("code") == "scope_unavailable"


def test_invalid_period_returns_400(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(),
    )
    _patch_user(monkeypatch)
    response = settlements_client.get(
        "/financeiro/settlements/payables?start_date=bad&end_date=2026-01-31",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 400
    assert response.json().get("success") is False


def test_missing_period_returns_400(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(),
    )
    _patch_user(monkeypatch)
    response = settlements_client.get(
        "/financeiro/settlements/payables", headers=S2S_HEADERS
    )
    assert response.status_code == 400


def test_happy_path_returns_items_envelope(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(),
    )
    _patch_user(monkeypatch)

    from app.application.dto.financeiro_settlements.settlements_response import (
        SettlementQuality,
        SettlementsListResponse,
    )
    from app.application.use_cases.financeiro_settlements.normalize import (
        normalize_settlement_item,
    )

    item = normalize_settlement_item(
        {
            "settlement_id": "ID1",
            "settlement_date": "20260110",
            "settlement_amount": "10.00",
            "currency_code": "BRL",
            "nature_code": "100",
            "nature_description": "FORNECEDORES",
            "source_branch": "",
            "missing_document": 0,
            "missing_nature": 0,
        }
    )
    fake_result = SettlementsListResponse(
        report="financial-settlements-payables",
        side="payable",
        period={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="complete",
        quality=SettlementQuality(),
        pagination={"page": 1, "page_size": 50, "total_items": 1},
        sort={"sort_by": "settlement_date", "sort_dir": "desc"},
        items=[item],
    )
    use_case = MagicMock()
    use_case.execute.return_value = fake_result

    # Bypass the fail-closed resolver only for the wiring test.
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.settlements_router."
        "build_get_settlements_use_case",
        lambda: use_case,
    )
    response = settlements_client.get(
        f"/financeiro/settlements/payables?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_settlements_payables"
    data = body["data"]
    assert data["items"][0]["branchCode"] is None
    assert data["items"][0]["linkStatus"] == "resolved"
    assert data["officialTotals"] is False
    use_case.execute.assert_called_once()
    kwargs = use_case.execute.call_args.kwargs
    assert kwargs["side"] == "payable"
    assert kwargs["user_subject"] == "user-1"


def test_receivables_happy_path_operation_id(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)

    from app.application.dto.financeiro_settlements.settlements_response import (
        SettlementQuality,
        SettlementsListResponse,
    )

    fake_result = SettlementsListResponse(
        report="financial-settlements-receivables",
        side="receivable",
        period={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="complete",
        quality=SettlementQuality(),
        pagination={"page": 1, "page_size": 50, "total_items": 0},
        sort={"sort_by": "settlement_date", "sort_dir": "desc"},
        items=[],
    )
    use_case = MagicMock()
    use_case.execute.return_value = fake_result
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.settlements_router."
        "build_get_settlements_use_case",
        lambda: use_case,
    )
    response = settlements_client.get(
        f"/financeiro/settlements/receivables?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    assert (
        response.json()["meta"]["operationId"]
        == "get_financeiro_settlements_receivables"
    )
    assert use_case.execute.call_args.kwargs["side"] == "receivable"


def test_summary_happy_path_operation_id(
    settlements_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)

    from app.application.dto.financeiro_settlements.settlements_response import (
        SettlementQuality,
        SettlementsSummaryResponse,
    )

    fake_result = SettlementsSummaryResponse(
        report="financial-settlements-summary",
        period={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="complete",
        quality=SettlementQuality(),
        groups=[],
    )
    use_case = MagicMock()
    use_case.execute.return_value = fake_result
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.settlements_router."
        "build_get_settlements_summary_use_case",
        lambda: use_case,
    )
    response = settlements_client.get(
        f"/financeiro/settlements/summary?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert (
        body["meta"]["operationId"] == "get_financeiro_settlements_summary"
    )
    assert body["data"]["officialTotals"] is False


def test_service_principal_as_user_does_not_unlock(
    settlements_client: TestClient, monkeypatch
) -> None:
    """Legacy internal-token principal (principal_type='service') stays a
    non-human actor; scope resolver still blocks — never treated as user."""
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(),
    )
    _patch_user(monkeypatch, principal_type="service")
    response = settlements_client.get(
        f"/financeiro/settlements/payables?{PERIOD}", headers=S2S_HEADERS
    )
    # resolver receives user_subject=None and stays unresolved → 403
    assert response.status_code == 403
