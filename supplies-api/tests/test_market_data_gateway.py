"""MarketDataGateway transport tests (PROC-0076)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
import requests

from app.infrastructure.gateways.market_data_gateway import (
    MarketDataGateway,
    MarketDataGatewayError,
)


class _Response:
    def __init__(self, status_code: int, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _gateway(transport) -> MarketDataGateway:
    provider = MagicMock()
    provider.get_token.return_value = "s2s-token"
    return MarketDataGateway(
        base_url="http://external-data:8000",
        transport=transport,
        token_provider=provider,
    )


def test_service_authorization_header_sent():
    calls = []

    def transport(url, *, headers, timeout, params=None):
        calls.append((url, headers))
        return _Response(200, {"items": [], "page_info": {}})

    gw = _gateway(transport)
    gw.catalog()
    assert calls[0][1]["X-Delpi-Service-Authorization"] == "Bearer s2s-token"


def test_metal_observations_paginates_until_no_cursor():
    seen_cursors = []

    def transport(url, *, headers, timeout, params=None):
        cursor = params.get("cursor")
        seen_cursors.append(cursor)
        if cursor is None:
            return _Response(
                200,
                {
                    "items": [{"id": 1}],
                    "page_info": {"next_cursor": "abc"},
                },
            )
        return _Response(
            200, {"items": [{"id": 2}], "page_info": {"next_cursor": None}}
        )

    gw = _gateway(transport)
    items = gw.metal_observations(
        "copper", date(2026, 1, 1), date(2026, 12, 31)
    )
    assert items == [{"id": 1}, {"id": 2}]
    assert seen_cursors == [None, "abc"]


def test_fx_observations_chunks_over_366_days():
    windows = []

    def transport(url, *, headers, timeout, params=None):
        windows.append((params["date_from"], params["date_to"]))
        return _Response(200, {"items": [], "page_info": {}})

    gw = _gateway(transport)
    gw.fx_observations(
        "ptax_closing_sell", date(2025, 1, 1), date(2026, 6, 30)
    )
    assert len(windows) == 2
    # 366-day inclusive window: 2025-01-01 .. 2026-01-01
    assert windows[0] == ("2025-01-01", "2026-01-01")
    assert windows[1] == ("2026-01-02", "2026-06-30")


def test_timeout_maps_to_504():
    def transport(url, *, headers, timeout, params=None):
        raise requests.Timeout("slow")

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 504
    assert exc.value.code == "upstream_timeout"


def test_connection_error_maps_to_503():
    def transport(url, *, headers, timeout, params=None):
        raise requests.ConnectionError("refused")

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 503


def test_429_carries_retry_after():
    def transport(url, *, headers, timeout, params=None):
        return _Response(
            429, {"detail": "slow down"}, headers={"Retry-After": "45"}
        )

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 429
    assert exc.value.retry_after == 45


def test_4xx_passthrough_with_upstream_code():
    def transport(url, *, headers, timeout, params=None):
        return _Response(403, {"code": "forbidden"})

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 403
    assert exc.value.code == "forbidden"


def test_5xx_passthrough():
    def transport(url, *, headers, timeout, params=None):
        return _Response(500, {"code": "internal_error"})

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 500


def test_invalid_json_is_502():
    def transport(url, *, headers, timeout, params=None):
        return _Response(200, ValueError("not json"))

    with pytest.raises(MarketDataGatewayError) as exc:
        _gateway(transport).catalog()
    assert exc.value.status_code == 502
    assert exc.value.code == "invalid_response"


def test_s2s_token_failure_maps_to_503():
    from delpi_auth.service_errors import ServiceAuthError

    provider = MagicMock()
    provider.get_token.side_effect = ServiceAuthError("no token")
    gw = MarketDataGateway(
        base_url="http://x",
        transport=lambda **kw: None,
        token_provider=provider,
    )
    with pytest.raises(MarketDataGatewayError) as exc:
        gw.catalog()
    assert exc.value.status_code == 503
    assert exc.value.code == "s2s_unavailable"
