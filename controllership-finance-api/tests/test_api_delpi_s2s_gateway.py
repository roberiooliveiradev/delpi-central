"""S2S gateway — client-credentials provider, headers, fail-closed errors."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from delpi_auth.service_errors import ServiceAuthConfigError

from controllership_finance_app.infrastructure import api_delpi_gateway as gw
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    ApiDelpiSettlementsGateway,
    DelpiApiGatewayError,
)


@pytest.fixture(autouse=True)
def _reset_provider():
    gw.reset_s2s_token_provider()
    yield
    gw.reset_s2s_token_provider()


def _gateway_with_token(token="s2s-jwt"):
    provider = MagicMock()
    provider.get_token.return_value = token
    return ApiDelpiSettlementsGateway(
        token_provider=provider, base_url="http://api-delpi:8000"
    )


def test_headers_carry_user_bearer_plus_service_jwt():
    gateway = _gateway_with_token("SVC123")
    headers = gateway._build_headers("user-jwt-9")
    assert headers["Authorization"] == "Bearer user-jwt-9"
    assert headers["X-Delpi-Service-Authorization"] == "Bearer SVC123"
    assert headers["X-Delpi-Caller-App"] == "controllership-finance-api"
    # shared internal token never added
    assert "X-Delpi-Service-Token" not in headers


def test_token_failure_fails_closed():
    provider = MagicMock()
    provider.get_token.side_effect = ServiceAuthConfigError(
        "S2S_CLIENT_ID missing"
    )
    gateway = ApiDelpiSettlementsGateway(
        token_provider=provider, base_url="http://api-delpi:8000"
    )
    with pytest.raises(DelpiApiGatewayError):
        gateway._build_headers("user-jwt")


def test_unconfigured_env_fails_closed(monkeypatch):
    monkeypatch.setenv("S2S_TOKEN_URL", "")
    monkeypatch.setenv("S2S_CLIENT_ID", "")
    monkeypatch.setenv("S2S_CLIENT_SECRET", "")
    gateway = ApiDelpiSettlementsGateway(base_url="http://api-delpi:8000")
    with pytest.raises(DelpiApiGatewayError):
        gateway._build_headers("user-jwt")


def _fake_response(status=200, body=None):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = body if body is not None else {"ok": True}
    return response


def test_get_sends_params_and_returns_json():
    gateway = _gateway_with_token()
    with patch.object(gw.requests, "get") as mock_get:
        mock_get.return_value = _fake_response(200, {"data": [1]})
        result = gateway.get(
            "/financeiro/settlements/payables",
            access_token="u",
            params={"start_date": "2026-01-01"},
        )
    assert result == {"data": [1]}
    kwargs = mock_get.call_args.kwargs
    assert kwargs["params"] == {"start_date": "2026-01-01"}
    assert kwargs["timeout"] == gateway.timeout


def test_upstream_403_extracts_error_code():
    gateway = _gateway_with_token()
    with patch.object(gw.requests, "get") as mock_get:
        mock_get.return_value = _fake_response(
            403,
            {
                "success": False,
                "message": "Escopo de dados financeiros não autorizado.",
                "error": {"code": "scope_unavailable", "recoverable": False},
            },
        )
        with pytest.raises(DelpiApiGatewayError) as exc_info:
            gateway.get("/x", access_token="u")
    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "scope_unavailable"


def test_upstream_5xx_and_timeout_fail_closed():
    gateway = _gateway_with_token()
    with patch.object(gw.requests, "get") as mock_get:
        mock_get.return_value = _fake_response(503, {"success": False})
        with pytest.raises(DelpiApiGatewayError) as exc_info:
            gateway.get("/x", access_token="u")
        assert exc_info.value.status_code == 503

    import requests as real_requests

    with patch.object(
        gw.requests, "get", side_effect=real_requests.Timeout()
    ):
        with pytest.raises(DelpiApiGatewayError):
            gateway.get("/x", access_token="u")


def test_invalid_json_raises_gateway_error():
    gateway = _gateway_with_token()
    bad = MagicMock()
    bad.status_code = 200
    bad.json.side_effect = ValueError("no json")
    with patch.object(gw.requests, "get", return_value=bad):
        with pytest.raises(DelpiApiGatewayError):
            gateway.get("/x", access_token="u")
