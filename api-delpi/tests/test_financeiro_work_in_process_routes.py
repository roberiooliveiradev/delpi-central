"""HTTP contract for /financeiro/work-in-process — S2S + delegated user.

Same guard family as the sibling stock-inventory route: the
``stock-inventory.read`` scope on ``controllership-finance-api`` plus a
delegated human Bearer (ADR-010).
"""

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
ROUTE = "/financeiro/work-in-process"


@pytest.fixture
def work_in_process_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.work_in_process_router import (
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


def test_router_exposes_work_in_process_routes() -> None:
    from app.interface.http.routes.financeiro.work_in_process_router import (
        router,
    )

    assert router.prefix == ROUTE
    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert {ROUTE, f"{ROUTE}/export"} <= paths


def test_missing_service_header_returns_401(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 401


def test_wrong_client_returns_403(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_happy_path_returns_wip_envelope(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)

    from app.application.dto.financeiro_work_in_process.work_in_process_response import (
        WorkInProcessItem,
        WorkInProcessResponse,
        WorkInProcessTypeSummary,
    )

    fake_result = WorkInProcessResponse(
        report="work-in-process",
        period="2026-09",
        referenceDate="2026-09-30",
        dataAsOf="2026-09-30",
        branchCode="01",
        reportScope="all_products",
        status="available",
        branchesAvailable=["01"],
        branchesMissing=[],
        physicalTotal="702287.869000",
        allocatedTotal="169128.463000",
        grandTotal="871416.332000",
        pagination={"page": 1, "page_size": 50, "total_items": 1},
        parityStatus="PENDING",
        items=[
            WorkInProcessItem(
                branchCode="01",
                productCode="MP001",
                description="Matéria-prima",
                productType="MP",
                productionOrder="00012300101",
                allocatedQuantity="10.000000",
                allocatedValue="169128.463000",
            )
        ],
        summariesByType=[
            WorkInProcessTypeSummary(
                productType="MP",
                physicalValue="702287.869000",
                allocatedValue="169128.463000",
                totalValue="871416.332000",
                openOrderCount=1,
            )
        ],
    )
    use_case = MagicMock()
    use_case.execute.return_value = fake_result
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.work_in_process_router."
        "build_work_in_process_use_case",
        lambda: use_case,
    )
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}&branch=01", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_work_in_process"
    data = body["data"]
    assert data["status"] == "available"
    assert data["officialMatr989"] is False
    assert data["grandTotal"] == "871416.332000"
    assert data["items"][0]["productionOrder"] == "00012300101"
    use_case.execute.assert_called_once()
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"


def test_service_principal_as_user_does_not_unlock(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = work_in_process_client.get(
        f"{ROUTE}?{PERIOD}", headers=S2S_HEADERS
    )
    assert response.status_code == 403


def test_export_invalid_format_returns_400(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = work_in_process_client.get(
        f"{ROUTE}/export?{PERIOD}&format=xlsx", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def test_export_streams_document_bytes(
    work_in_process_client: TestClient, monkeypatch
) -> None:
    """export_financeiro_work_in_process — authenticated bytes passthrough."""
    import io

    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "stream": io.BytesIO(b"%PDF-fake"),
        "content_type": "application/pdf",
        "filename": "r08-work-in-process-2026-09-01-all_products.pdf",
        "exported_count": 3,
    }
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.work_in_process_router."
        "build_export_work_in_process_use_case",
        lambda: use_case,
    )
    response = work_in_process_client.get(
        f"{ROUTE}/export?{PERIOD}&branch=01&format=pdf",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["X-Exported-Count"] == "3"
    assert response.content == b"%PDF-fake"
    kwargs = use_case.execute.call_args.kwargs
    assert kwargs["export_format"] == "pdf"
    assert kwargs["user_subject"] == "user-1"
