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
    COMMERCIAL_API_ROOT_PATH: str = _get_env(
        "COMMERCIAL_API_ROOT_PATH",
        default="/apps/commercial-api",
    )
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    COMMERCIAL_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("COMMERCIAL_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    COMMERCIAL_PORTFOLIO_SOURCE: str = (
        str(_get_env("COMMERCIAL_PORTFOLIO_SOURCE", default="legacy") or "legacy").lower()
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    DELPI_API_URL: str = _get_env("DELPI_API_URL", default="http://delpi-api-delpi:8000")
    DELPI_API_TIMEOUT: str = _get_env("DELPI_API_TIMEOUT", default="30")
    DELPI_API_CALLER_APP: str = _get_env("DELPI_API_CALLER_APP", default="commercial-api")

    CORE_API_BASE_URL: str = _get_env(
        "CORE_API_BASE_URL",
        "DELPI_AUTH_CORE_API_URL",
        default="http://core-api:8000",
    )
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        "CORE_API_SERVICE_TOKEN",
        default="",
    )
    CORE_API_TIMEOUT: str = _get_env("CORE_API_TIMEOUT", default="10")
    COMMERCIAL_PORTAL_NOTIFICATIONS_ENABLED: bool = (
        str(
            _get_env("COMMERCIAL_PORTAL_NOTIFICATIONS_ENABLED", default="true") or "true"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    # Poll ready_to_invoice + task-due scans (portal/toast). Badge does not need this.
    COMMERCIAL_INTEGRATION_JOBS_SCHEDULER_ENABLED: bool = (
        str(
            _get_env(
                "COMMERCIAL_INTEGRATION_JOBS_SCHEDULER_ENABLED", default="true"
            )
            or "true"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    COMMERCIAL_INTEGRATION_JOBS_POLL_SECONDS: float = float(
        _get_env("COMMERCIAL_INTEGRATION_JOBS_POLL_SECONDS", default="60") or "60"
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    COMMERCIAL_AVATAR_UPLOAD_DIR: str = _get_env(
        "COMMERCIAL_AVATAR_UPLOAD_DIR",
        default="/app/data/commercial-avatars",
    )
    COMMERCIAL_ATTACHMENT_UPLOAD_DIR: str = _get_env(
        "COMMERCIAL_ATTACHMENT_UPLOAD_DIR",
        default="/app/data/commercial-attachments",
    )
    COMMERCIAL_USER_AVATAR_UPLOAD_DIR: str = _get_env(
        "COMMERCIAL_USER_AVATAR_UPLOAD_DIR",
        default="/app/data/commercial-user-avatars",
    )
    PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR: str | None = _get_env(
        "PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR",
    )


settings = Settings()
