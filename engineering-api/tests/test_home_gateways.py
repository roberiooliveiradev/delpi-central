"""F2a.S5 — adapters oficiais com httpx.MockTransport (sem rede).

Verifica normalização item→HomeItem, headers de delegação oficial,
mapeamento 401/403 → forbidden e falhas → unavailable com reason.
"""

from __future__ import annotations

import httpx
import pytest

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
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
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
