# shared/delpi_auth/jwt_validator.py

from jose import jwt
import requests
import os

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080/auth")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "delpi")

DISCOVERY_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

_jwks_cache = None
_jwks_uri = None


def _get_jwks():

    global _jwks_cache
    global _jwks_uri

    if _jwks_cache:
        return _jwks_cache

    # Descobre endpoints automaticamente
    if not _jwks_uri:
        discovery = requests.get(DISCOVERY_URL)
        discovery.raise_for_status()

        data = discovery.json()
        _jwks_uri = data["jwks_uri"]

    response = requests.get(_jwks_uri)
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