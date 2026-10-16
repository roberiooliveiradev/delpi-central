"""Gateway S2S de notificações — configured vs empty token."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from production_pulse_app.domain.errors import (
    NotificationGatewayUnauthorized,
    NotificationGatewayUnavailable,
)
from production_pulse_app.infrastructure.gateways.core_api_notification_gateway import (
    CoreApiNotificationGateway,
)


class _Handler(httpx.BaseTransport):
    def __init__(self, status: int = 200, body: dict[str, Any] | None = None) -> None:
        self.status = status
        self.body = body or {"success": True}
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)


def test_dispatch_posts_with_service_token():
    handler = _Handler()
    client = httpx.Client(transport=handler)
    gw = CoreApiNotificationGateway(
        base_url="http://core-api:8000",
        service_token="secret-token",
        client=client,
    )
    result = gw.dispatch({"category": "production_pulse_device_offline", "title": "t"})
    assert result["success"] is True
    assert len(handler.requests) == 1
    assert handler.requests[0].headers["X-Delpi-Service-Token"] == "secret-token"
    assert handler.requests[0].url.path.endswith("/integrations/notifications")


def test_empty_token_raises_unavailable():
    gw = CoreApiNotificationGateway(base_url="http://core-api:8000", service_token="")
    with pytest.raises(NotificationGatewayUnavailable):
        gw.dispatch({"category": "x"})


def test_unauthorized_maps_to_domain_error():
    handler = _Handler(status=401)
    client = httpx.Client(transport=handler)
    gw = CoreApiNotificationGateway(
        base_url="http://core-api:8000",
        service_token="bad",
        client=client,
    )
    with pytest.raises(NotificationGatewayUnauthorized):
        gw.dispatch({"category": "x"})
