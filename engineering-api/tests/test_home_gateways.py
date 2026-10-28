"""F2a.S5 — adapters oficiais com httpx.MockTransport (sem rede).

Verifica normalização item→HomeItem, headers de delegação oficial,
mapeamento 401/403 → forbidden e falhas → unavailable com reason.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from delpi_auth.context_resolver import resolve_user_context
from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as downstream_jwt_middleware,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.api_delpi_gateway import (
    ApiDelpiLmpSource,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)
from engineering_app.infrastructure.gateways.requests_api_gateway import (
    RequestsApiMineSource,
    RequestsApiWorkQueueSource,
)

CTX = HomeSourceContext(
    user_id="user-1", access_token="user-jwt-1", request_id="req-1"
)


def _capture(handler):
    captured = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return handler(request)

    return captured, _handler


def _requests_payload(items, total=None):
    return {
        "success": True,
        "data": {
            "items": items,
            "total": len(items) if total is None else total,
            "page": 1,
            "page_size": 50,
        },
    }


def _request_item(**over):
    item = {
        "id": "req-abc",
        "request_number": "000456",
        "type_code": "raw-material-creation",
        "status": "submitted",
        "status_alias": "Em análise",
        "priority": "normal",
        "branch_code": "01",
        "allowed_actions": ["comment"],
        "created_at": "2026-10-20T09:00:00Z",
        "updated_at": "2026-10-25T11:00:00Z",
    }
    item.update(over)
    return item


async def test_work_queue_maps_items_and_delegation(monkeypatch):
    # F2a.R1: token interno CONFIGURADO — não pode vazar no header da
    # chamada personalizada nem alterar a delegação do usuário.
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-internal-test")
    captured, handler = _capture(
        lambda req: httpx.Response(
            200, json=_requests_payload([_request_item()], total=42)
        )
    )
    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )

    result = await source.fetch(CTX, limit=5)

    assert result.status == "available"
    assert result.total == 42
    item = result.items[0]
    assert item.id == "req-abc"
    assert item.kind == "task"
    assert item.title == "000456"
    assert item.status == "submitted"
    assert item.status_label == "Em análise"
    assert item.date == "2026-10-25T11:00:00Z"
    assert item.source == "requests-api"
    assert item.href == "/apps/my-requests"
    assert item.meta["type_code"] == "raw-material-creation"

    request = captured["request"]
    assert request.url.path == "/requests/work-queue"
    assert request.url.params["page_size"] == "5"
    assert request.headers["Authorization"] == "Bearer user-jwt-1"
    assert request.headers["X-Delpi-Caller-App"] == "engineering-api"
    assert request.headers["X-Request-Id"] == "req-1"
    assert "x-delpi-service-token" not in request.headers


async def test_mine_source_uses_mine_endpoint(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(200, json=_requests_payload([]))
    )
    source = RequestsApiMineSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )

    result = await source.fetch(CTX, limit=5)

    assert result.status == "empty"
    assert result.total == 0
    assert captured["request"].url.path == "/requests/mine"


async def test_requests_forbidden_maps_to_forbidden(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(
            403, json={"success": False, "message": "forbidden"}
        )
    )
    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "forbidden"
    assert result.items == ()


async def test_requests_5xx_maps_to_unavailable(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(503, text="Service Unavailable")
    )
    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "unavailable"
    assert result.reason == "upstream_error"


async def test_requests_timeout_maps_to_unavailable(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")

    def handler(request):
        raise httpx.ConnectTimeout("boom")

    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "unavailable"
    assert result.reason == "timeout"


async def test_requests_bad_envelope_maps_contract_error(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(200, json={"success": True, "data": {}})
    )
    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "unavailable"
    assert result.reason == "contract_error"


async def test_lmp_source_maps_official_fields(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    lmp = {
        "sale_number": "LMP-777",
        "sale_description": "Prensa reforma",
        "engineering_status": "waiting_engineering",
        "branch": "01",
        "costumer_name": "Cliente X",
        "reference_revision": "4",
        "measurement_revision": "1",
        "start_date": "2026-10-01",
        "end_date": "2026-11-01",
    }
    captured, handler = _capture(
        lambda req: httpx.Response(
            200,
            json={
                "success": True,
                "data": {"items": [lmp], "total": 3, "total_pages": 1},
                "meta": {"operationId": "list_lmps"},
            },
        )
    )
    source = ApiDelpiLmpSource(
        DownstreamClient(
            "http://delpi-api-delpi:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )

    result = await source.fetch(CTX, limit=5)

    assert result.status == "available"
    assert result.total == 3
    item = result.items[0]
    assert item.id == "LMP-777"
    assert item.kind == "lmp"
    assert item.title == "Prensa reforma"
    assert item.status == "waiting_engineering"
    assert item.date == "2026-11-01"
    assert item.source == "api-delpi"
    assert item.href == "/apps/dashboard-lmps"
    assert item.meta["reference_revision"] == "4"
    assert captured["request"].url.path == "/engineering/lmps"


async def test_lmp_forbidden_maps_to_forbidden(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(
            403, json={"success": False, "message": "Forbidden"}
        )
    )
    source = ApiDelpiLmpSource(
        DownstreamClient(
            "http://delpi-api-delpi:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "forbidden"
    assert result.items == ()


async def test_lmp_item_without_sale_number_is_contract_error(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
    captured, handler = _capture(
        lambda req: httpx.Response(
            200,
            json={"success": True, "data": {"items": [{"foo": 1}], "total": 1}},
        )
    )
    source = ApiDelpiLmpSource(
        DownstreamClient(
            "http://delpi-api-delpi:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "unavailable"
    assert result.reason == "contract_error"


# ------------------------------------------------------------------
# F2a.R1 — delegação de identidade humana (security rework)
# ------------------------------------------------------------------


def _downstream_probe_app() -> FastAPI:
    """Boundary AuthN real de um owner downstream.

    `requests-api` e `api-delpi` delegam ao `jwt_middleware` compartilhado
    de `delpi_auth` nas rotas de dados — o mesmo código executado aqui.
    A rota expõe o principal efetivamente reconhecido pelo owner.
    """
    app = FastAPI()
    app.middleware("http")(downstream_jwt_middleware)

    @app.get("/resource", operation_id="test_owner_principal_probe")
    def _whoami():
        user = resolve_user_context()
        return {
            "success": True,
            "data": {
                "principal_type": getattr(user, "principal_type", None),
                "is_superadmin": getattr(user, "is_superadmin", None),
            },
        }

    return app


async def test_adapters_never_send_internal_service_token(monkeypatch):
    """Header isolation: com o token interno configurado, os três
    adapters enviam apenas o Bearer do usuário + metadados."""
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-internal-test")
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200, json=_requests_payload([], total=0)
        )

    transport = httpx.MockTransport(handler)
    sources = (
        RequestsApiWorkQueueSource(
            DownstreamClient(
                "http://requests-api:8000",
                timeout_seconds=2.0,
                transport=transport,
            )
        ),
        RequestsApiMineSource(
            DownstreamClient(
                "http://requests-api:8000",
                timeout_seconds=2.0,
                transport=transport,
            )
        ),
        ApiDelpiLmpSource(
            DownstreamClient(
                "http://delpi-api-delpi:8000",
                timeout_seconds=2.0,
                transport=transport,
            )
        ),
    )
    for source in sources:
        await source.fetch(CTX, limit=5)

    assert len(captured) == 3
    for request in captured:
        assert request.headers["Authorization"] == "Bearer user-jwt-1"
        assert request.headers["X-Delpi-Caller-App"] == "engineering-api"
        assert request.headers["X-Request-Id"] == "req-1"
        assert "x-delpi-service-token" not in request.headers


async def test_client_reaches_owner_as_user_principal_with_service_token_configured(
    monkeypatch, jwks_env, core_rbac
):
    """Contrato de delegação humana: o middleware REAL do owner
    (compartilhado) resolve o JWT humano como principal `user`, mesmo
    com `API_DELPI_INTERNAL_SERVICE_TOKEN` configurado."""
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-internal-test")
    token = jwks_env["make_token"](sub="user-ana")
    client = DownstreamClient(
        "http://owner",
        timeout_seconds=2.0,
        transport=httpx.ASGITransport(app=_downstream_probe_app()),
    )

    data = await client.get("/resource", access_token=token)

    assert data["principal_type"] == "user"
    assert data["is_superadmin"] is False


async def test_service_token_would_elevate_but_client_never_sends_it(
    monkeypatch, jwks_env, core_rbac
):
    """Controle negativo contra o middleware real do owner.

    (a) Se `X-Delpi-Service-Token` fosse enviado, o shared short-circuit
    ANTES do JWT produziria principal `service` + `is_superadmin` —
    a superfície de risco removida.
    (b) O DownstreamClient corrigido não carrega esse header.
    """
    svc = "svc-internal-test"
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", svc)
    token = jwks_env["make_token"](sub="user-ana")
    probe = _downstream_probe_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=probe), base_url="http://owner"
    ) as raw:
        elevated = await raw.get(
            "/resource",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Delpi-Service-Token": svc,
            },
        )
    assert elevated.status_code == 200
    assert elevated.json()["data"]["principal_type"] == "service"
    assert elevated.json()["data"]["is_superadmin"] is True

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_requests_payload([], total=0))

    client = DownstreamClient(
        "http://owner",
        timeout_seconds=2.0,
        transport=httpx.MockTransport(handler),
    )
    await client.get("/resource", access_token=token)
    assert captured[0].headers["Authorization"] == f"Bearer {token}"
    assert "x-delpi-service-token" not in captured[0].headers


async def test_requests_401_maps_to_forbidden_without_fallback(monkeypatch):
    """401 do owner = acesso negado — nunca elevação nem `available`."""
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-internal-test")
    source = RequestsApiWorkQueueSource(
        DownstreamClient(
            "http://requests-api:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(
                lambda req: httpx.Response(
                    401, json={"success": False, "message": "unauthorized"}
                )
            ),
        )
    )
    result = await source.fetch(CTX, limit=5)
    assert result.status == "forbidden"
    assert result.items == ()
