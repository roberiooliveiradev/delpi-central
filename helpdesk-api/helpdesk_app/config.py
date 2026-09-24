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
    HELPDESK_API_ROOT_PATH: str = _get_env(
        "HELPDESK_API_ROOT_PATH", default="/apps/helpdesk-api"
    )
    PORT: str = _get_env("PORT", default="8000")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    PUBLIC_BASE_URL: str = _get_env("PUBLIC_BASE_URL", default="") or ""
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    HELPDESK_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("HELPDESK_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    CORE_API_URL: str = _get_env(
        "DELPI_AUTH_CORE_API_URL", "CORE_API_URL", default="http://core-api:8000"
    )
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        "API_DELPI_INTERNAL_SERVICE_TOKEN",
        default="",
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")

    GLPI_BASE_URL: str = _get_env(
        "GLPI_BASE_URL", default="https://helpdesk.centraldelpi.com.br"
    )
    GLPI_OAUTH_CLIENT_ID: str = _get_env("GLPI_OAUTH_CLIENT_ID", default="") or ""
    GLPI_OAUTH_CLIENT_SECRET: str = _get_env("GLPI_OAUTH_CLIENT_SECRET", default="") or ""
    GLPI_OAUTH_REDIRECT_URI: str = _get_env(
        "GLPI_OAUTH_REDIRECT_URI",
        default="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
    )
    GLPI_SAML_IDP_ID: str = _get_env("GLPI_SAML_IDP_ID", default="1") or ""
    HELPDESK_TOKEN_ENCRYPTION_KEY: str = (
        _get_env("HELPDESK_TOKEN_ENCRYPTION_KEY", default="") or ""
    )
    GLPI_HTTP_CONNECT_TIMEOUT: float = float(
        _get_env("GLPI_HTTP_CONNECT_TIMEOUT", default="5") or "5"
    )
    GLPI_HTTP_READ_TIMEOUT: float = float(
        _get_env("GLPI_HTTP_READ_TIMEOUT", default="20") or "20"
    )
    # H12 exception (product-authorized): legacy apirest Document upload only.
    GLPI_LEGACY_UPLOAD_ENABLED: bool = (
        str(_get_env("GLPI_LEGACY_UPLOAD_ENABLED", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    GLPI_LEGACY_APP_TOKEN: str = _get_env("GLPI_LEGACY_APP_TOKEN", default="") or ""
    GLPI_LEGACY_USER_TOKEN: str = _get_env("GLPI_LEGACY_USER_TOKEN", default="") or ""
    GLPI_LEGACY_MAX_UPLOAD_BYTES: int = int(
        _get_env("GLPI_LEGACY_MAX_UPLOAD_BYTES", default=str(20 * 1024 * 1024))
        or str(20 * 1024 * 1024)
    )
    # Perfis GLPI atribuíveis como «Técnico» (default Technician = 6). CSV de ids.
    GLPI_ASSIGNEE_PROFILE_IDS: str = (
        _get_env("GLPI_ASSIGNEE_PROFILE_IDS", default="6") or "6"
    )


settings = Settings()


def parse_assignee_profile_ids(raw: str | None = None) -> tuple[int, ...]:
    text = (raw if raw is not None else settings.GLPI_ASSIGNEE_PROFILE_IDS) or ""
    ids: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            continue
        if value > 0 and value not in ids:
            ids.append(value)
    return tuple(ids) if ids else (6,)
