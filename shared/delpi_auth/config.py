# shared/delpi_auth/config.py
import os

CORE_API_URL = os.getenv("CORE_API_URL", "http://core-api:8000")
CORE_ME_ENDPOINT = f"{CORE_API_URL}/core-api/me"

KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL")
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER")
KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE")