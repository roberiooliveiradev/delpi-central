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
    PRODUCTION_PULSE_API_ROOT_PATH: str = _get_env(
        "PRODUCTION_PULSE_API_ROOT_PATH", default="/apps/production-pulse-api"
    )
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(
            _get_env("PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false"
        ).lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    CORE_API_URL: str = _get_env(
        "DELPI_AUTH_CORE_API_URL", "CORE_API_URL", default="http://core-api:8000"
    )
    CORE_API_SERVICE_TOKEN: str = _get_env(
        "CORE_API_SERVICE_TOKEN", "API_DELPI_INTERNAL_SERVICE_TOKEN", default=""
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    PP_POLL_MAX_CONCURRENT: int = int(_get_env("PP_POLL_MAX_CONCURRENT", default="10") or "10")
    PP_ONLINE_GRACE_MIN_SECONDS: int = int(
        _get_env("PP_ONLINE_GRACE_MIN_SECONDS", default="60") or "60"
    )
    PP_ONLINE_GRACE_MAX_SECONDS: int = int(
        _get_env("PP_ONLINE_GRACE_MAX_SECONDS", default="600") or "600"
    )
    PP_ONLINE_GRACE_MULTIPLIER: int = int(
        _get_env("PP_ONLINE_GRACE_MULTIPLIER", default="2") or "2"
    )

    DELPI_API_URL: str = _get_env(
        "DELPI_API_URL", default="http://delpi-api-delpi:8000"
    )
    DELPI_API_TIMEOUT: float = float(_get_env("DELPI_API_TIMEOUT", default="30") or "30")
    DELPI_API_CALLER_APP: str = _get_env(
        "DELPI_API_CALLER_APP", default="production-pulse-api"
    )
    PP_WORK_CENTER_CACHE_TTL_SECONDS: int = int(
        _get_env("PP_WORK_CENTER_CACHE_TTL_SECONDS", default="300") or "300"
    )

    PP_POLL_SCHEDULER_ENABLED: bool = (
        str(_get_env("PP_POLL_SCHEDULER_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    # Preenchido após instanciação (env ou content JSON).
    PP_POLL_SCHEDULER_TICK_MS: int | None = None


def _optional_positive_int(raw: str | None) -> int | None:
    if raw is None or raw == "":
        return None
    value = int(raw)
    if value < 1:
        return None
    return value


settings = Settings()
# Override opcional; None → device_validation_content.json → schedulerTickMs.default
settings.PP_POLL_SCHEDULER_TICK_MS = _optional_positive_int(
    _get_env("PP_POLL_SCHEDULER_TICK_MS", default="")
)
