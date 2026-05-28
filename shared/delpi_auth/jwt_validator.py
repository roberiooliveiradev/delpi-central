# shared/delpi_auth/jwt_validator.py

from jose import jwt
import requests
import os

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080/auth")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "delpi")

DISCOVERY_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

_jwks_cache = None


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

    jwks = _get_jwks()

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

    if not key:
        raise Exception("Invalid token key")

    _audience = os.getenv("KEYCLOAK_AUDIENCE")

    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=_audience if _audience else None,
        options={"verify_aud": bool(_audience)},
    )

    return payload