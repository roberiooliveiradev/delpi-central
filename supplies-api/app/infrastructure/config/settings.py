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
    CORE_API_INTEGRATIONS_SERVICE_TOKEN = (
        os.getenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN")
        or os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN")
        or ""
    )

    DELPI_API_URL = os.getenv("DELPI_API_URL", "http://delpi-api-delpi:8000")
    DELPI_API_TIMEOUT_SECONDS = float(os.getenv("DELPI_API_TIMEOUT", "30"))
    SUPPLIES_CALLER_APP = (
        os.getenv("SUPPLIES_CALLER_APP")
        or os.getenv("DELPI_API_CALLER_APP")
        or "supplies-api"
    )
    DELPI_API_CALLER_APP = SUPPLIES_CALLER_APP

    # Individual S2S credential for migrated calls into api-delpi.
    # Missing values keep the mechanism disabled — the S2S gateway fails
    # closed and never falls back to the shared internal token.
    S2S_TOKEN_URL = os.getenv("S2S_TOKEN_URL", "")
    S2S_CLIENT_ID = os.getenv("S2S_CLIENT_ID", "")
    S2S_CLIENT_SECRET = os.getenv("S2S_CLIENT_SECRET", "")
    S2S_SCOPE = os.getenv("S2S_SCOPE", "")
    S2S_TIMEOUT_SECONDS = float(os.getenv("S2S_TIMEOUT_SECONDS", "10"))

    PURCHASE_REQUESTS_API_URL = os.getenv(
        "PURCHASE_REQUESTS_API_URL",
        "http://delpi-purchase-requests-api:8000",
    )
    PURCHASE_REQUESTS_API_TIMEOUT_SECONDS = float(
        os.getenv("PURCHASE_REQUESTS_API_TIMEOUT", "90")
    )
    STRATEGIC_INDICATORS_API_BASE_URL = os.getenv(
        "STRATEGIC_INDICATORS_API_BASE_URL",
        "http://strategic-indicators-api:8000",
    )
    STRATEGIC_INDICATORS_API_TIMEOUT_SECONDS = float(
        os.getenv("STRATEGIC_INDICATORS_API_TIMEOUT", "30")
    )

    POSTAL_ADDRESS_PROVIDER_URL = os.getenv(
        "POSTAL_ADDRESS_PROVIDER_URL", "https://viacep.com.br/ws"
    )
    POSTAL_ADDRESS_FALLBACK_URL = os.getenv(
        "POSTAL_ADDRESS_FALLBACK_URL", "https://brasilapi.com.br/api/cep/v1"
    )
    POSTAL_ADDRESS_TIMEOUT_SECONDS = float(
        os.getenv("POSTAL_ADDRESS_TIMEOUT", "6")
    )

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
    def s2s_configured(cls) -> bool:
        return bool(cls.S2S_TOKEN_URL and cls.S2S_CLIENT_ID and cls.S2S_CLIENT_SECRET)

    @classmethod
    def plugins_db_configured(cls) -> bool:
        return bool(
            cls.PLUGINS_DB_HOST
            and cls.PLUGINS_DB_NAME
            and cls.PLUGINS_DB_USER
            and cls.PLUGINS_DB_PASSWORD
        )
