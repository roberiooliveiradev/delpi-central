# app/security/jwt_validator.py

from jose import jwt
from jose.exceptions import JWTError
import requests
from app.config import settings

ALGORITHMS = ["RS256"]
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    response = requests.get(settings.KEYCLOAK_JWKS_URL)
    response.raise_for_status()
    _jwks_cache = response.json()
    return _jwks_cache


def validate_token(token: str) -> dict:
    jwks = get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=ALGORITHMS,
            audience=settings.KEYCLOAK_AUDIENCE,
            issuer=settings.KEYCLOAK_ISSUER,
        )
        return payload
    except JWTError:
        raise ValueError("Invalid token")