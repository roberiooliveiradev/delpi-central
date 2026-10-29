"""HTTP contract for /financeiro/stock-inventory — S2S + delegated user + scope."""

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
ROUTE = "/financeiro/stock-inventory"


@pytest.fixture
def stock_inventory_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.stock_inventory_router import router

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


def test_router_exposes_stock_inventory_route() -> None:
    from app.interface.http.routes.financeiro.stock_inventory_router import router

    assert router.prefix == ROUTE
    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert {ROUTE, f"{ROUTE}/export"} <= paths
    assert any(ROUTE in (route.path or "") for route in router.routes)


def test_missing_service_header_returns_401(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 401


def test_wrong_client_returns_403(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    """A settlements.read token is NOT authorized for stock-inventory."""
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    """FINANCEIRO_STOCK_INVENTORY_ENABLED stays off by default: valid S2S +
    delegated user still gets `scope_unavailable`, never real rows."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_invalid_period_returns_400(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = stock_inventory_client.get(
        f"{ROUTE}?period=bad", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def test_happy_path_returns_snapshot_envelope(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)

    from app.application.dto.financeiro_stock_inventory.stock_inventory_response import (
        StockInventoryItem,
        StockInventoryResponse,
    )

    fake_result = StockInventoryResponse(
        report="stock-inventory",
        period="2026-09",
        referenceDate="2026-09-30",
        dataAsOf="2026-09-30",
        branchCode="02",
        reportScope="all_products",
        status="available",
        branchesAvailable=["02"],
        branchesMissing=[],
        historicalTotal="10576487.8400",
        pagination={"page": 1, "page_size": 50, "total_items": 1},
        stockTotal="10576487.8400",
        processPhysicalTotal="0.000000",
        processAllocatedTotal="0.000000",
        processTotal="0.000000",
        grandTotal="10576487.8400",
        parityStatus="PENDING",
        items=[
            StockInventoryItem(
                productCode="P1",
                description="Produto 1",
                productType="MP",
                productGroup="1000",
                unit="KG",
                warehouse="01",
                branchCode="02",
                historicalQuantity="10.0000",
                historicalStockValue="100.5000",
            )
        ],
    )
    use_case = MagicMock()
    use_case.execute.return_value = fake_result
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.stock_inventory_router."
        "build_stock_inventory_use_case",
        lambda: use_case,
    )
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}&branch=02", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_stock_inventory"
    data = body["data"]
    assert data["status"] == "available"
    assert data["officialP7"] is False
    assert data["parityStatus"] == "PENDING"
    assert data["stockTotal"] == "10576487.8400"
    assert data["processTotal"] == "0.000000"
    assert data["grandTotal"] == "10576487.8400"
    assert data["items"][0]["productCode"] == "P1"
    use_case.execute.assert_called_once()
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.reference_date() == "20260930"
    assert request_arg.branch == "02"


def test_service_principal_as_user_does_not_unlock(
    stock_inventory_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = stock_inventory_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403
