"""Verification of individual service-to-service tokens.

A service token is a Keycloak client-credentials JWT. Cryptographic trust
(signature, issuer, audience, expiry) is delegated to the shared JWT
validator; this module adds the S2S-specific policy:

- the technical client (``azp``/``client_id``) must be in the allowlist;
- every required operation scope must be granted;
- missing mandatory configuration fails closed.

It never consults the legacy shared secret and never mints a superadmin
principal.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Mapping

import requests
from jose import JWTError

from .jwt_validator import JwtConfigurationError, validate_token
from .service_errors import (
    ServiceAuthConfigError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
    ServiceTokenMissingError,
    ServiceValidatorUnavailableError,
)
from .service_identity import ServiceIdentity

S2S_AUDIENCE_ENV = "S2S_AUDIENCE"
S2S_ALLOWED_CLIENTS_ENV = "S2S_ALLOWED_CLIENTS"


def _client_id_from_claims(claims: Mapping[str, object]) -> str:
    """Technical client identifier: ``azp`` first, then ``client_id``."""
    for claim in ("azp", "client_id"):
        value = str(claims.get(claim) or "").strip()
        if value:
            return value
    return ""


@dataclass(frozen=True)
class ServiceTokenValidatorConfig:
    audience: str
    allowed_clients: frozenset[str]

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "ServiceTokenValidatorConfig":
        env = environ if environ is not None else os.environ
        audience = (env.get(S2S_AUDIENCE_ENV) or "").strip()
        allowed_clients = frozenset(
            item.strip()
            for item in (env.get(S2S_ALLOWED_CLIENTS_ENV) or "").split(",")
            if item.strip()
        )
        missing = []
        if not audience:
            missing.append(S2S_AUDIENCE_ENV)
        if not allowed_clients:
            missing.append(S2S_ALLOWED_CLIENTS_ENV)
        if missing:
            raise ServiceAuthConfigError(
                "Missing S2S validator configuration: " + ", ".join(missing)
            )
        return cls(audience=audience, allowed_clients=allowed_clients)


class ServiceTokenValidator:
    def __init__(self, config: ServiceTokenValidatorConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "ServiceTokenValidator":
        return cls(ServiceTokenValidatorConfig.from_env(environ))

    def validate(
        self,
        token: str | None,
        *,
        required_scopes: Iterable[str] = (),
        allowed_clients: Iterable[str] | None = None,
    ) -> ServiceIdentity:
        if not token or not token.strip():
            raise ServiceTokenMissingError()

        try:
            claims = validate_token(token, expected_audience=self._config.audience)
        except JwtConfigurationError as exc:
            raise ServiceAuthConfigError(str(exc)) from exc
        except requests.RequestException as exc:
            raise ServiceValidatorUnavailableError() from exc
        except (JWTError, ValueError) as exc:
            raise ServiceTokenInvalidError() from exc

        client_id = _client_id_from_claims(claims)
        permitted = (
            frozenset(allowed_clients)
            if allowed_clients is not None
            else self._config.allowed_clients
        )
        if not client_id or client_id not in permitted:
            raise ServiceClientDeniedError()

        identity = ServiceIdentity.from_claims(claims, client_id=client_id)
        if not identity.subject:
            raise ServiceTokenInvalidError()

        missing_scopes = {scope for scope in required_scopes if scope not in identity.scopes}
        if missing_scopes:
            raise ServiceScopeDeniedError()

        return identity
