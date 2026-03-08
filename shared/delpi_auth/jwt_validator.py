# shared/delpi_auth/jwt_validator.py

from jose import jwt
from jose.exceptions import JWTError
import requests

from .config import KEYCLOAK_JWKS_URL, KEYCLOAK_ISSUER, KEYCLOAK_AUDIENCE

ALGORITHMS = ["RS256"]
_jwks_cache = None


def _get_jwks():
    global _jwks_cache

    if _jwks_cache:
        return _jwks_cache

    response = requests.get(KEYCLOAK_JWKS_URL, timeout=5)
    response.raise_for_status()

    _jwks_cache = response.json()

    return _jwks_cache


def validate_token(token: str) -> dict:
    jwks = _get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=ALGORITHMS,
            audience=KEYCLOAK_AUDIENCE,
            issuer=KEYCLOAK_ISSUER,
        )

        return payload

    except JWTError as e:
        raise Exception("Invalid token") from e