"""Typed errors for individual service-to-service authentication.

Every error carries a stable ``code`` for safe observability — log codes and
client ids, never token material.
"""

from __future__ import annotations


class ServiceAuthError(RuntimeError):
    code = "S2S_ERROR"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)


class ServiceAuthConfigError(ServiceAuthError):
    """Mandatory S2S configuration is absent — fail closed."""

    code = "S2S_CONFIG_MISSING"


class ServiceTokenMissingError(ServiceAuthError):
    code = "S2S_TOKEN_MISSING"


class ServiceTokenInvalidError(ServiceAuthError):
    """Signature, issuer, audience or expiry failed cryptographic checks."""

    code = "S2S_TOKEN_INVALID"


class ServiceValidatorUnavailableError(ServiceAuthError):
    """JWKS/discovery endpoint unreachable — transient dependency, fail closed."""

    code = "S2S_VALIDATOR_UNAVAILABLE"


class ServiceClientDeniedError(ServiceAuthError):
    """Valid token, but the technical client is not in the allowlist."""

    code = "S2S_CLIENT_DENIED"


class ServiceScopeDeniedError(ServiceAuthError):
    """Valid client, but the operation scope is not granted."""

    code = "S2S_SCOPE_DENIED"


class ServiceTokenRequestError(ServiceAuthError):
    """The token endpoint refused or failed the credentials grant."""

    code = "S2S_TOKEN_REQUEST_FAILED"

    def __init__(self, message: str | None = None, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class ServiceTokenResponseError(ServiceAuthError):
    """The token endpoint answered 200 but the payload is not a token."""

    code = "S2S_TOKEN_RESPONSE_INVALID"
