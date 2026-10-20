from __future__ import annotations

from unittest.mock import patch

import pytest
import requests
from jose import ExpiredSignatureError, JWTError

from delpi_auth import service_token_validator as validator_module
from delpi_auth.jwt_validator import JwtConfigurationError
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
    ServiceTokenMissingError,
    ServiceValidatorUnavailableError,
)
from delpi_auth.service_token_validator import (
    ServiceTokenValidator,
    ServiceTokenValidatorConfig,
)

CONFIG = ServiceTokenValidatorConfig(
    audience="api-delpi",
    allowed_clients=frozenset({"supplies-api"}),
)

ENV = {
    "S2S_AUDIENCE": "api-delpi",
    "S2S_ALLOWED_CLIENTS": "supplies-api, purchase-requests-api",
}


def _claims(**overrides):
    claims = {
        "iss": "https://portal.example/auth/realms/delpi",
        "aud": "api-delpi",
        "azp": "supplies-api",
        "sub": "service-account-subject",
        "scope": "suppliers.read profile",
        "exp": 1893456000,
    }
    claims.update(overrides)
    return claims


def _patch_decode(claims):
    return patch.object(validator_module, "validate_token", return_value=claims)


def test_from_env_requires_audience():
    with pytest.raises(ServiceAuthConfigError, match="S2S_AUDIENCE"):
        ServiceTokenValidator.from_env({"S2S_ALLOWED_CLIENTS": "supplies-api"})


def test_from_env_requires_allowed_clients():
    with pytest.raises(ServiceAuthConfigError, match="S2S_ALLOWED_CLIENTS"):
        ServiceTokenValidator.from_env({"S2S_AUDIENCE": "api-delpi"})


def test_from_env_builds_config():
    validator = ServiceTokenValidator.from_env(ENV)
    assert validator._config.audience == "api-delpi"
    assert validator._config.allowed_clients == frozenset(
        {"supplies-api", "purchase-requests-api"}
    )


def test_validate_returns_identity_for_allowed_client():
    with _patch_decode(_claims()) as decode:
        identity = ServiceTokenValidator(CONFIG).validate("token", required_scopes=("suppliers.read",))
    decode.assert_called_once_with("token", expected_audience="api-delpi")
    assert identity.client_id == "supplies-api"
    assert identity.subject == "service-account-subject"
    assert identity.principal_type == "service"
    assert not hasattr(identity, "is_superadmin")
    assert identity.scopes == frozenset({"suppliers.read", "profile"})
    assert identity.audience == ("api-delpi",)


def test_validate_rejects_missing_token():
    with pytest.raises(ServiceTokenMissingError):
        ServiceTokenValidator(CONFIG).validate(None)
    with pytest.raises(ServiceTokenMissingError):
        ServiceTokenValidator(CONFIG).validate("   ")


def test_validate_rejects_invalid_signature_or_audience():
    for exc in (JWTError("bad signature"), ExpiredSignatureError("expired"), ValueError("key")):
        with patch.object(validator_module, "validate_token", side_effect=exc):
            with pytest.raises(ServiceTokenInvalidError):
                ServiceTokenValidator(CONFIG).validate("token")


def test_validate_maps_jwks_fetch_failure_to_unavailable():
    with patch.object(
        validator_module,
        "validate_token",
        side_effect=requests.ConnectionError("jwks unreachable"),
    ):
        with pytest.raises(ServiceValidatorUnavailableError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_validate_rejects_unknown_client():
    with _patch_decode(_claims(azp="financial-api")):
        with pytest.raises(ServiceClientDeniedError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_validate_rejects_missing_client_claim():
    with _patch_decode(_claims(azp=None, client_id=None)):
        with pytest.raises(ServiceClientDeniedError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_validate_accepts_client_id_claim_fallback():
    with _patch_decode(_claims(azp=None, client_id="supplies-api")):
        identity = ServiceTokenValidator(CONFIG).validate("token")
    assert identity.client_id == "supplies-api"


def test_validate_rejects_user_token_client():
    # A portal user JWT carries azp=delpi-central — never a trusted S2S client.
    with _patch_decode(_claims(azp="delpi-central")):
        with pytest.raises(ServiceClientDeniedError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_validate_rejects_insufficient_scope():
    with _patch_decode(_claims(scope="profile")):
        with pytest.raises(ServiceScopeDeniedError):
            ServiceTokenValidator(CONFIG).validate("token", required_scopes=("suppliers.read",))


def test_validate_rejects_missing_scope_claim():
    with _patch_decode(_claims(scope=None)):
        with pytest.raises(ServiceScopeDeniedError):
            ServiceTokenValidator(CONFIG).validate("token", required_scopes=("suppliers.read",))


def test_validate_rejects_missing_subject():
    with _patch_decode(_claims(sub="")):
        with pytest.raises(ServiceTokenInvalidError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_validate_route_scoped_client_override():
    with _patch_decode(_claims(azp="supplies-api")):
        with pytest.raises(ServiceClientDeniedError):
            ServiceTokenValidator(CONFIG).validate(
                "token", allowed_clients=("other-api",)
            )


def test_validate_passes_config_error_through():
    with patch.object(
        validator_module,
        "validate_token",
        side_effect=JwtConfigurationError("no issuer"),
    ):
        with pytest.raises(ServiceAuthConfigError):
            ServiceTokenValidator(CONFIG).validate("token")


def test_audience_list_claim_normalized():
    with _patch_decode(_claims(aud=["api-delpi", "account"])):
        identity = ServiceTokenValidator(CONFIG).validate("token")
    assert identity.audience == ("api-delpi", "account")
