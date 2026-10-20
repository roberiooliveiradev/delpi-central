from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceTokenRequestError,
    ServiceTokenResponseError,
)
from delpi_auth.service_token_provider import (
    ClientCredentialsTokenProvider,
    ServiceTokenProviderConfig,
)

CONFIG = ServiceTokenProviderConfig(
    token_url="https://idp.example/realms/delpi/protocol/openid-connect/token",
    client_id="supplies-api",
    client_secret="test-client-secret",
    scopes=("suppliers.read",),
    timeout_seconds=5.0,
)


def _response(status=200, payload=None, json_error=False):
    response = Mock(spec=requests.Response)
    response.status_code = status
    if json_error:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = payload or {}
    return response


class _Clock:
    def __init__(self):
        self.now = 1_000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_from_env_requires_token_url_client_and_secret():
    with pytest.raises(ServiceAuthConfigError, match="S2S_TOKEN_URL"):
        ServiceTokenProviderConfig.from_env({})
    with pytest.raises(ServiceAuthConfigError, match="S2S_CLIENT_ID"):
        ServiceTokenProviderConfig.from_env({"S2S_TOKEN_URL": "https://idp/token"})
    with pytest.raises(ServiceAuthConfigError, match="S2S_CLIENT_SECRET"):
        ServiceTokenProviderConfig.from_env(
            {"S2S_TOKEN_URL": "https://idp/token", "S2S_CLIENT_ID": "supplies-api"}
        )


def test_from_env_parses_scope_and_timeout():
    config = ServiceTokenProviderConfig.from_env(
        {
            "S2S_TOKEN_URL": "https://idp/token",
            "S2S_CLIENT_ID": "supplies-api",
            "S2S_CLIENT_SECRET": "test-client-secret",
            "S2S_SCOPE": "suppliers.read suppliers.write",
            "S2S_TIMEOUT_SECONDS": "3.5",
        }
    )
    assert config.scopes == ("suppliers.read", "suppliers.write")
    assert config.timeout_seconds == 3.5


def test_get_token_posts_client_credentials_grant():
    http_post = Mock(return_value=_response(payload={"access_token": "jwt-1", "expires_in": 300}))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())

    assert provider.get_token() == "jwt-1"

    http_post.assert_called_once()
    call = http_post.call_args
    assert call.args[0] == CONFIG.token_url
    assert call.kwargs["timeout"] == 5.0
    assert call.kwargs["data"]["grant_type"] == "client_credentials"
    assert call.kwargs["data"]["client_id"] == "supplies-api"
    assert call.kwargs["data"]["scope"] == "suppliers.read"


def test_get_token_reuses_cache_until_early_margin():
    clock = _Clock()
    http_post = Mock(return_value=_response(payload={"access_token": "jwt-1", "expires_in": 300}))
    provider = ClientCredentialsTokenProvider(
        CONFIG, http_post=http_post, clock=clock, refresh_margin_seconds=30
    )

    provider.get_token()
    clock.advance(269)  # still inside usable window (300 - 30 margin)
    assert provider.get_token() == "jwt-1"
    assert http_post.call_count == 1

    clock.advance(2)  # crosses the refresh margin → fetch again
    http_post.return_value = _response(payload={"access_token": "jwt-2", "expires_in": 300})
    assert provider.get_token() == "jwt-2"
    assert http_post.call_count == 2


def test_get_token_invalidate_forces_refresh():
    http_post = Mock(return_value=_response(payload={"access_token": "jwt-1", "expires_in": 300}))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    provider.get_token()
    provider.invalidate()
    provider.get_token()
    assert http_post.call_count == 2


def test_get_token_maps_http_error_to_request_error():
    http_post = Mock(return_value=_response(status=401, payload={"error": "invalid_client"}))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    with pytest.raises(ServiceTokenRequestError) as err:
        provider.get_token()
    assert err.value.status_code == 401
    assert "jwt" not in str(err.value)


def test_get_token_maps_network_failure_to_request_error():
    http_post = Mock(side_effect=requests.ConnectionError("down"))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    with pytest.raises(ServiceTokenRequestError):
        provider.get_token()


def test_get_token_maps_timeout_to_request_error():
    http_post = Mock(side_effect=requests.Timeout("slow"))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    with pytest.raises(ServiceTokenRequestError):
        provider.get_token()


def test_get_token_rejects_malformed_json():
    http_post = Mock(return_value=_response(json_error=True))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    with pytest.raises(ServiceTokenResponseError):
        provider.get_token()


def test_get_token_rejects_missing_access_token():
    http_post = Mock(return_value=_response(payload={"token_type": "Bearer"}))
    provider = ClientCredentialsTokenProvider(CONFIG, http_post=http_post, clock=_Clock())
    with pytest.raises(ServiceTokenResponseError):
        provider.get_token()


def test_get_token_uses_fallback_expiry_when_absent():
    clock = _Clock()
    http_post = Mock(return_value=_response(payload={"access_token": "jwt-1"}))
    provider = ClientCredentialsTokenProvider(
        CONFIG, http_post=http_post, clock=clock, refresh_margin_seconds=30
    )
    provider.get_token()
    clock.advance(29)
    assert provider.get_token() == "jwt-1"
    clock.advance(2)
    provider.get_token()
    assert http_post.call_count == 2


def test_no_scope_param_when_unset():
    config = ServiceTokenProviderConfig(
        token_url="https://idp/token",
        client_id="supplies-api",
        client_secret="test-client-secret",
    )
    http_post = Mock(return_value=_response(payload={"access_token": "jwt-1", "expires_in": 300}))
    provider = ClientCredentialsTokenProvider(config, http_post=http_post, clock=_Clock())
    provider.get_token()
    assert "scope" not in http_post.call_args.kwargs["data"]
