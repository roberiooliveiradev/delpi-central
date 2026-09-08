from __future__ import annotations

from unittest.mock import patch

import pytest

from delpi_auth import jwt_validator


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    jwt_validator._jwks_cache = None
    yield
    jwt_validator._jwks_cache = None


def test_decode_requires_audience(monkeypatch):
    monkeypatch.delenv("KEYCLOAK_AUDIENCE", raising=False)
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://portal.example/auth/realms/delpi")

    with pytest.raises(jwt_validator.JwtConfigurationError, match="KEYCLOAK_AUDIENCE"):
        jwt_validator._decode_token("token")


def test_decode_requires_issuer(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.delenv("KEYCLOAK_ISSUER", raising=False)

    with pytest.raises(jwt_validator.JwtConfigurationError, match="KEYCLOAK_ISSUER"):
        jwt_validator._decode_token("token")


def test_decode_passes_audience_issuer_and_algorithms_to_jose(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://portal.example/auth/realms/delpi")
    monkeypatch.setenv("JWT_ALGORITHMS", "RS256")

    jwks = {"keys": [{"kid": "key-1", "kty": "RSA"}]}
    claims = {"sub": "user-1"}

    with (
        patch.object(jwt_validator, "_get_jwks", return_value=jwks),
        patch.object(jwt_validator.jwt, "get_unverified_header", return_value={"kid": "key-1"}),
        patch.object(jwt_validator.jwt, "decode", return_value=claims) as decode,
    ):
        assert jwt_validator._decode_token("token") == claims

    decode.assert_called_once_with(
        "token",
        jwks["keys"][0],
        algorithms=["RS256"],
        audience="delpi-central",
        issuer="https://portal.example/auth/realms/delpi",
    )


def test_multiple_algorithms_are_explicitly_parsed(monkeypatch):
    monkeypatch.setenv("JWT_ALGORITHMS", "RS256, RS512")
    assert jwt_validator._allowed_algorithms() == ["RS256", "RS512"]


def test_configuration_error_does_not_retry_jwks(monkeypatch):
    monkeypatch.delenv("KEYCLOAK_AUDIENCE", raising=False)
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://portal.example/auth/realms/delpi")

    with patch.object(jwt_validator, "_get_jwks") as get_jwks:
        with pytest.raises(jwt_validator.JwtConfigurationError):
            jwt_validator.validate_token("token")

    get_jwks.assert_not_called()


def test_decode_rejects_unknown_kid_after_required_config(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://portal.example/auth/realms/delpi")

    with (
        patch.object(jwt_validator, "_get_jwks", return_value={"keys": [{"kid": "known"}]}),
        patch.object(jwt_validator.jwt, "get_unverified_header", return_value={"kid": "unknown"}),
    ):
        with pytest.raises(ValueError, match="Invalid token key"):
            jwt_validator._decode_token("token")
