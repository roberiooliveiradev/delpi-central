# shared/delpi_auth/jwt_validator.py

from __future__ import annotations

import os

import requests
from jose import jwt

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080/auth")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "delpi")

DISCOVERY_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

_jwks_cache = None


class JwtConfigurationError(RuntimeError):
    """Raised when mandatory JWT validation configuration is missing."""


def _required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise JwtConfigurationError(
            f"Missing required JWT configuration: {name}. "
            "Protected APIs must fail closed instead of disabling token validation."
        )
    return value


def _allowed_algorithms() -> list[str]:
    configured = (os.getenv("JWT_ALGORITHMS") or "RS256").strip()
    algorithms = [item.strip() for item in configured.split(",") if item.strip()]
    if not algorithms:
        raise JwtConfigurationError(
            "Missing required JWT configuration: JWT_ALGORITHMS"
        )
    return algorithms


def _resolve_jwks_url() -> str:
    configured = (os.getenv("KEYCLOAK_JWKS_URL") or "").strip()
    if configured:
        return configured

    discovery = requests.get(DISCOVERY_URL, timeout=10)
    discovery.raise_for_status()
    jwks_uri = discovery.json()["jwks_uri"]

    if "localhost:8080" in jwks_uri or "127.0.0.1:8080" in jwks_uri:
        return (
            f"{KEYCLOAK_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
        )

    return jwks_uri


def _get_jwks():
    global _jwks_cache

    if _jwks_cache:
        return _jwks_cache

    response = requests.get(_resolve_jwks_url(), timeout=10)
    response.raise_for_status()

    _jwks_cache = response.json()
    return _jwks_cache


def validate_token(token: str):
    try:
        return _decode_token(token)
    except JwtConfigurationError:
        # Configuration errors cannot be fixed by refreshing JWKS and must fail closed.
        raise
    except Exception:
        # A single JWKS refresh preserves the existing key-rotation recovery behavior.
        global _jwks_cache
        _jwks_cache = None
        return _decode_token(token)


def _decode_token(token: str):
    audience = _required_env("KEYCLOAK_AUDIENCE")
    issuer = _required_env("KEYCLOAK_ISSUER")
    algorithms = _allowed_algorithms()

    jwks = _get_jwks()

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    key = next((item for item in jwks["keys"] if item["kid"] == kid), None)
    if not key:
        raise ValueError("Invalid token key")

    return jwt.decode(
        token,
        key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
    )
