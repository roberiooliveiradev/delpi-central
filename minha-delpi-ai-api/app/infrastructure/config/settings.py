import os


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "minha-delpi-ai-api")
    ENV = os.getenv("FLASK_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "")
    KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "")
    JWT_ALGORITHMS = os.getenv("JWT_ALGORITHMS", "RS256")
