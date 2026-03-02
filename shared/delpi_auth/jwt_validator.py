from jose import jwt
from jose.exceptions import JWTError
import requests
import json

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


def _extract_permissions(payload: dict) -> list[str]:
    perms = payload.get("delpi_permissions", [])

    if isinstance(perms, str):
        try:
            perms = json.loads(perms)
        except Exception:
            perms = []

    if not isinstance(perms, list):
        return []

    return perms


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
        print("JWT ERROR:", e)
        raise