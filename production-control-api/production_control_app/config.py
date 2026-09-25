import os

from dotenv import load_dotenv

load_dotenv()


def _get_env(*names: str, default=None):
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


class Settings:
    PC_API_ROOT_PATH: str = _get_env("PC_API_ROOT_PATH", default="/apps/production-control-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    PC_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("PC_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")

    PC_PRODUCT_3D_MODELS_DIR: str = _get_env(
        "PC_PRODUCT_3D_MODELS_DIR", default="/app/data/product-3d-models"
    )
    PC_PRODUCT_3D_MAX_BYTES: int = int(
        _get_env("PC_PRODUCT_3D_MAX_BYTES", default=str(25 * 1024 * 1024))
    )

    DELPI_API_URL: str = _get_env("DELPI_API_URL", default="http://delpi-api-delpi:8000")
    DELPI_API_TIMEOUT: float = float(_get_env("DELPI_API_TIMEOUT", default="30"))
    DELPI_API_CALLER_APP: str = _get_env("DELPI_API_CALLER_APP", default="production-control-api")

    # Integração MES → Production Pulse (snapshot de contador).
    # Dev (pulse em network_mode:host): http://host.docker.internal:80/apps/production-pulse-api
    # Prod (mesma delpi-network): http://delpi-production-pulse-api:8000
    PRODUCTION_PULSE_API_URL: str = _get_env(
        "PRODUCTION_PULSE_API_URL",
        default="http://delpi-production-pulse-api:8000",
    )
    PRODUCTION_PULSE_API_TIMEOUT: float = float(
        _get_env("PRODUCTION_PULSE_API_TIMEOUT", default="5")
    )
    PC_PRODUCTION_RUN_POLL_MS: int = int(
        _get_env("PC_PRODUCTION_RUN_POLL_MS", default="500") or "500"
    )
    PC_BENCH_SESSION_TTL_HOURS: int = int(
        _get_env("PC_BENCH_SESSION_TTL_HOURS", default="12") or "12"
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")


settings = Settings()
