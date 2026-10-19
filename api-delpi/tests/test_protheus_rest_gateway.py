"""Tests — Protheus REST gateway (auth, supplier, timeout, redaction)."""

from __future__ import annotations

import logging

import httpx
import pytest

from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway


def _config() -> ProtheusRestConfig:
    return ProtheusRestConfig(
        username="tech.user",
        password="secret-value",
        base_url="https://protheus.example/rest",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/delpi/api/v1/suppliers/",
    )


def test_request_access_token_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "password=secret-value" in str(request.url)
        assert "username=tech.user" in str(request.url)
        return httpx.Response(
            200,
            json={
                "access_token": "tok-abc",
                "refresh_token": "ref-xyz",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    gateway = ProtheusRestGateway(client=client, sleep=lambda _: None)
    token = gateway.request_access_token(_config())
    assert token.access_token == "tok-abc"
    assert token.expires_in == 3600


def test_auth_failure_does_not_embed_secrets_in_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": "invalid_grant"})

    gateway = ProtheusRestGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    with pytest.raises(ProtheusRestError) as exc:
        gateway.request_access_token(_config())
    assert exc.value.code == "PROTHEUS_AUTH_FAILED"
    assert "secret-value" not in str(exc.value)
    assert "tok-" not in str(exc.value)


def test_get_supplier_existing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer tok-abc"
        assert request.url.path.endswith("/00000101")
        return httpx.Response(200, json={"A2_COD": "000001", "A2_LOJA": "01"})

    gateway = ProtheusRestGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    data = gateway.get_supplier(
        _config(), supplier_id="00000101", access_token="tok-abc"
    )
    assert data["A2_COD"] == "000001"


def test_get_supplier_not_found_code_002() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "002", "message": "not found"})

    gateway = ProtheusRestGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    with pytest.raises(ProtheusRestError) as exc:
        gateway.get_supplier(_config(), supplier_id="99999999", access_token="tok")
    assert exc.value.code == "PROTHEUS_SUPPLIER_NOT_FOUND"
    assert exc.value.status_code == 404


def test_timeout_maps_to_controlled_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    gateway = ProtheusRestGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    with pytest.raises(ProtheusRestError) as exc:
        gateway.request_access_token(_config())
    assert exc.value.code == "PROTHEUS_TIMEOUT"


def test_external_http_error_maps_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    gateway = ProtheusRestGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    with pytest.raises(ProtheusRestError) as exc:
        gateway.request_access_token(_config())
    assert exc.value.code == "PROTHEUS_UNAVAILABLE"


def test_httpx_request_logger_is_quiet_to_avoid_oauth_query_leak() -> None:
    # Import side effect: gateway module must silence httpx/httpcore INFO URL logs.
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
