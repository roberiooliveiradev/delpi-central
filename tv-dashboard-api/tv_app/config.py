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
    TV_DASHBOARD_API_ROOT_PATH: str = _get_env(
        "TV_DASHBOARD_API_ROOT_PATH",
        default="/apps/tv-dashboard-api",
    )
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    TV_DASHBOARD_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("TV_DASHBOARD_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    TV_DASHBOARD_PUBLIC_PATH: str = _get_env(
        "TV_DASHBOARD_PUBLIC_PATH",
        default="/p/tv-dashboard/present",
    )

    DELPI_API_URL: str = _get_env("DELPI_API_URL", default="http://delpi-api-delpi:8000")
    DELPI_API_CALLER_APP: str = _get_env("DELPI_API_CALLER_APP", default="tv-dashboard-api")

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    TV_DASHBOARD_MEDIA_UPLOAD_DIR: str = _get_env(
        "TV_DASHBOARD_MEDIA_UPLOAD_DIR",
        default="/app/data/tv-dashboard/media",
    )

    CORE_API_BASE_URL: str = _get_env("CORE_API_BASE_URL", default="http://core-api:8000")
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        default="",
    )
    TV_DASHBOARD_NOTIFICATIONS_ENABLED: bool = (
        str(_get_env("TV_DASHBOARD_NOTIFICATIONS_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )

    # Sync OpenAPI api-delpi → tv_data_routes.json (startup + endpoint)
    TV_OPENAPI_SYNC_ON_STARTUP: bool = (
        str(_get_env("TV_OPENAPI_SYNC_ON_STARTUP", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    TV_OPENAPI_SYNC_TIMEOUT_SECONDS: float = float(
        _get_env("TV_OPENAPI_SYNC_TIMEOUT_SECONDS", default="45") or "45"
    )
    TV_DATA_ROUTES_PATH: str = _get_env(
        "TV_DATA_ROUTES_PATH",
        default="",
    ) or ""
    TV_OPENAPI_GENERATOR_SCRIPT: str = _get_env(
        "TV_OPENAPI_GENERATOR_SCRIPT",
        default="/app/tools/generate_tv_data_routes_from_openapi.py",
    ) or ""


settings = Settings()

# Propaga path do catálogo para o serviço de allowlist (resolve_routes_path).
if settings.TV_DATA_ROUTES_PATH:
    os.environ.setdefault("TV_DATA_ROUTES_PATH", settings.TV_DATA_ROUTES_PATH)
if settings.TV_OPENAPI_GENERATOR_SCRIPT:
    os.environ.setdefault(
        "TV_OPENAPI_GENERATOR_SCRIPT",
        settings.TV_OPENAPI_GENERATOR_SCRIPT,
    )
