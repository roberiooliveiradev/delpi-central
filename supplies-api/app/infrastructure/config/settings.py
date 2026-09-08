import os


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "supplies-api")
    ENV = os.getenv("ENV", os.getenv("FLASK_ENV", "development"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ROOT_PATH = os.getenv("SUPPLIES_API_ROOT_PATH", "/apps/supplies-api")

    KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "")
    KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "")
    JWT_ALGORITHMS = os.getenv("JWT_ALGORITHMS", "RS256")

    CORE_API_BASE_URL = os.getenv("CORE_API_BASE_URL", "http://core-api:8000")
    CORE_API_TIMEOUT_SECONDS = float(os.getenv("CORE_API_TIMEOUT", "10"))

    DELPI_API_URL = os.getenv("DELPI_API_URL", "http://delpi-api-delpi:8000")
    DELPI_API_TIMEOUT_SECONDS = float(os.getenv("DELPI_API_TIMEOUT", "30"))
    DELPI_API_CALLER_APP = os.getenv("DELPI_API_CALLER_APP", "supplies-api")

    RUN_MIGRATIONS_ON_STARTUP = (
        os.getenv("SUPPLIES_RUN_MIGRATIONS_ON_STARTUP", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    PLUGINS_DB_HOST = os.getenv("PLUGINS_DB_HOST", "")
    PLUGINS_DB_PORT = os.getenv("PLUGINS_DB_PORT", "5432")
    PLUGINS_DB_NAME = os.getenv("PLUGINS_DB_NAME", "")
    PLUGINS_DB_USER = os.getenv("PLUGINS_DB_USER", "")
    PLUGINS_DB_PASSWORD = os.getenv("PLUGINS_DB_PASSWORD", "")
    PLUGINS_DB_CONNECT_TIMEOUT = int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5"))
    PLUGINS_DB_SSLMODE = os.getenv("PLUGINS_DB_SSLMODE", "prefer")

    @classmethod
    def plugins_db_configured(cls) -> bool:
        return bool(
            cls.PLUGINS_DB_HOST
            and cls.PLUGINS_DB_NAME
            and cls.PLUGINS_DB_USER
            and cls.PLUGINS_DB_PASSWORD
        )
