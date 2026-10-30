"""HTTP contract for /financeiro/stock-kardex, /financeiro/inventory-
adjustments and /financeiro/cpv — S2S + delegated user + scope."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

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
    scopes=frozenset({"stock-inventory.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)

S2S_HEADERS = {
    "X-Delpi-Service-Authorization": "Bearer service-jwt",
    "X-Delpi-Caller-App": "controllership-finance-api",
    "Authorization": "Bearer user-jwt",
}

PERIOD = "period=2026-09"
KARDEX = "/financeiro/stock-kardex"
INVENT = "/financeiro/inventory-adjustments"
CPV = "/financeiro/cpv"


@pytest.fixture
def kardex_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.stock_kardex_router import (
        router,
    )

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
        "app.interface.http.routes.financeiro.stock_inventory_route_helpers."
        "resolve_user_context",
        lambda: user,
    )


def test_router_exposes_all_r06_r07_cpv_routes() -> None:
    from app.interface.http.routes.financeiro.stock_kardex_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert {
        f"{KARDEX}",
        f"{KARDEX}/summary",
        f"{KARDEX}/products/{{product_code}}",
        f"{KARDEX}/export",
        f"{INVENT}",
        f"{INVENT}/summary",
        f"{INVENT}/export",
        f"{CPV}",
    } <= paths
    operation_ids = {
        getattr(route, "operation_id", None) for route in router.routes
    }
    assert {
        "get_financeiro_stock_kardex",
        "get_financeiro_stock_kardex_summary",
        "get_financeiro_stock_kardex_product",
        "export_financeiro_stock_kardex",
        "get_financeiro_inventory_adjustments",
        "get_financeiro_inventory_adjustments_summary",
        "export_financeiro_inventory_adjustments",
        "get_financeiro_cpv",
    } <= operation_ids


def test_missing_service_header_returns_401(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_wrong_client_returns_403(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    kardex_client: TestClient, monkeypatch
) -> None:
    """A settlements.read token is NOT authorized for the kardex dataset."""
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    kardex_client: TestClient, monkeypatch
) -> None:
    """Dataset gate closed: valid S2S + delegated user still gets
    `scope_unavailable`, never real rows."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )

    monkeypatch.setattr(
        "app.composition.financeiro_stock_kardex_composer."
        "get_stock_inventory_scope_resolver",
        lambda: SharedDatasetStockInventoryScopeResolver(enabled=False),
    )
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_service_principal_as_user_does_not_unlock(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = kardex_client.get(f"{KARDEX}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_invalid_period_returns_400(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = kardex_client.get(
        f"{KARDEX}?period=bad", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def _fake_kardex_response():
    result = MagicMock()
    result.to_dict.return_value = {
        "report": "stock-kardex",
        "period": "2026-09",
        "status": "available",
        "parityStatus": "PENDING",
        "totals": {"movementCount": 1},
        "items": [{"productCode": "P1", "movementKind": "entry"}],
    }
    return result


def test_kardex_happy_path_envelope(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = _fake_kardex_response()
    import app.interface.http.routes.financeiro.stock_kardex_router as mod

    monkeypatch.setattr(mod, "build_stock_kardex_use_case", lambda: use_case)
    response = kardex_client.get(
        f"{KARDEX}?{PERIOD}&branch=02", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_stock_kardex"
    assert body["data"]["status"] == "available"
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"


def test_inventory_adjustments_forces_invent_kind(
    kardex_client: TestClient, monkeypatch
) -> None:
    """R07 route must constrain the shared engine to D3_DOC='INVENT'."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = _fake_kardex_response()
    import app.interface.http.routes.financeiro.stock_kardex_router as mod

    monkeypatch.setattr(mod, "build_stock_kardex_use_case", lambda: use_case)
    response = kardex_client.get(
        f"{INVENT}?{PERIOD}&branch=02&warehouse=01,99",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    assert (
        response.json()["meta"]["operationId"]
        == "get_financeiro_inventory_adjustments"
    )
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.document_kind == "invent"
    assert request_arg.requested_warehouses() == ("01", "99")


def test_export_streams_document_bytes(
    kardex_client: TestClient, monkeypatch
) -> None:
    import io

    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "stream": io.BytesIO(b"%PDF-fake"),
        "content_type": "application/pdf",
        "filename": "stock-kardex-2026-09-02.pdf",
        "exported_count": 7,
    }
    import app.interface.http.routes.financeiro.stock_kardex_router as mod

    monkeypatch.setattr(
        mod, "build_export_stock_kardex_use_case", lambda: use_case
    )
    response = kardex_client.get(
        f"{KARDEX}/export?{PERIOD}&format=pdf",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == b"%PDF-fake"
    kwargs = use_case.execute.call_args.kwargs
    assert kwargs["export_format"] == "pdf"
    assert kwargs["user_subject"] == "user-1"


def test_export_invalid_format_returns_400(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = kardex_client.get(
        f"{KARDEX}/export?{PERIOD}&format=xlsx",
        headers=S2S_HEADERS,
    )
    assert response.status_code in (400, 422)


def test_cpv_happy_path_envelope(
    kardex_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "report": "cpv",
        "status": "available",
        "asOfConvention": "live",
        "summary": {"cpvTotal": "100.000000"},
    }
    monkeypatch.setattr(
        "app.composition.financeiro_stock_kardex_composer."
        "build_financeiro_cpv_use_case",
        lambda: use_case,
    )
    response = kardex_client.get(
        f"{CPV}?{PERIOD}&branch=02", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_cpv"
    assert body["data"]["asOfConvention"] == "live"
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"
