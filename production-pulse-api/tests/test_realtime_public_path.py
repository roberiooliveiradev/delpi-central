from __future__ import annotations

from production_pulse_app.middleware.auth_middleware import _is_public


def test_realtime_ws_path_is_public_for_query_token():
    assert _is_public("/v1/realtime/ws") is True
    assert _is_public("/apps/production-pulse-api/v1/realtime/ws") is True
    assert _is_public("/devices") is False
    assert _is_public("/device-ota/check") is True
