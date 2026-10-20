from unittest.mock import Mock

import pytest
import responses

from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceTokenRequestError,
)

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_s2s_gateway import (
    DelpiS2SApiGateway,
    reset_s2s_token_provider,
)


def _provider(token="svc-jwt", error=None):
    provider = Mock()
    if error is not None:
        provider.get_token.side_effect = error
    else:
        provider.get_token.return_value = token
    return provider


def _gateway(provider, **kwargs):
    return DelpiS2SApiGateway(
        token_provider=provider,
        base_url="http://delpi-api.test",
        timeout_seconds=2.0,
        caller_app="supplies-api",
        **kwargs,
    )


@responses.activate
def test_s2s_get_sends_service_jwt_and_user_bearer_without_legacy_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "legacy-shared-secret")
    responses.add(
        responses.GET,
        "http://delpi-api.test/supplies/suppliers",
        json={"ok": True},
        status=200,
    )
    gateway = _gateway(_provider())

    data = gateway.get("/supplies/suppliers", access_token="user-jwt")

    assert data == {"ok": True}
    headers = responses.calls[0].request.headers
    assert headers["Authorization"] == "Bearer user-jwt"
    assert headers["X-Delpi-Service-Authorization"] == "Bearer svc-jwt"
    assert headers["X-Delpi-Caller-App"] == "supplies-api"
    assert "X-Delpi-Service-Token" not in headers


@responses.activate
def test_s2s_get_never_sends_shared_secret_even_when_env_set(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "legacy-shared-secret")
    responses.add(
        responses.GET,
        "http://delpi-api.test/x",
        json={"ok": True},
        status=200,
    )
    _gateway(_provider(token="jwt")).get("/x", access_token="u")
    for key in responses.calls[0].request.headers:
        assert "legacy-shared-secret" not in str(
            responses.calls[0].request.headers[key]
        )


@responses.activate
def test_s2s_provider_failure_fails_closed_without_request():
    gateway = _gateway(
        _provider(error=ServiceTokenRequestError("down", status_code=401))
    )
    with pytest.raises(DelpiApiGatewayError, match="s2s"):
        gateway.get("/supplies/suppliers", access_token="user-jwt")
    assert len(responses.calls) == 0


@responses.activate
def test_s2s_missing_config_fails_closed_without_request():
    gateway = _gateway(_provider(error=ServiceAuthConfigError("missing")))
    with pytest.raises(DelpiApiGatewayError):
        gateway.get("/supplies/suppliers", access_token="user-jwt")
    assert len(responses.calls) == 0


@responses.activate
def test_s2s_error_mapping_matches_base_gateway():
    responses.add(responses.GET, "http://delpi-api.test/x", status=503)
    with pytest.raises(DelpiApiGatewayError) as err:
        _gateway(_provider()).get("/x", access_token="u")
    assert err.value.status_code == 503

    responses.add(responses.GET, "http://delpi-api.test/y", status=403)
    with pytest.raises(DelpiApiGatewayError) as err:
        _gateway(_provider()).get("/y", access_token="u")
    assert err.value.status_code == 403


def test_shared_provider_from_env(monkeypatch):
    monkeypatch.setenv("S2S_TOKEN_URL", "https://idp.example/token")
    monkeypatch.setenv("S2S_CLIENT_ID", "supplies-api")
    monkeypatch.setenv("S2S_CLIENT_SECRET", "test-client-secret")
    reset_s2s_token_provider()
    try:
        from app.infrastructure.gateways.delpi_s2s_gateway import (
            get_s2s_token_provider,
        )

        provider = get_s2s_token_provider()
        assert provider is get_s2s_token_provider()
    finally:
        reset_s2s_token_provider()


def test_shared_provider_missing_env_fails_closed(monkeypatch):
    for name in ("S2S_TOKEN_URL", "S2S_CLIENT_ID", "S2S_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    reset_s2s_token_provider()
    try:
        from app.infrastructure.gateways.delpi_s2s_gateway import (
            get_s2s_token_provider,
        )

        with pytest.raises(ServiceAuthConfigError):
            get_s2s_token_provider()
    finally:
        reset_s2s_token_provider()
