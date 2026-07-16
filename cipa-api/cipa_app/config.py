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
    CIPA_API_ROOT_PATH: str = _get_env("CIPA_API_ROOT_PATH", default="/apps/cipa-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    CIPA_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("CIPA_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
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
    CORE_API_SERVICE_TOKEN: str = _get_env("CORE_API_SERVICE_TOKEN", "API_DELPI_INTERNAL_SERVICE_TOKEN", default="")

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    CIPA_SIGNATURE_UPLOAD_DIR: str = _get_env(
        "CIPA_SIGNATURE_UPLOAD_DIR", default="/app/data/cipa/signatures"
    )
    CIPA_ATTACHMENT_UPLOAD_DIR: str = _get_env(
        "CIPA_ATTACHMENT_UPLOAD_DIR", default="/app/data/cipa/attachments"
    )
    CIPA_PDF_UPLOAD_DIR: str = _get_env(
        "CIPA_PDF_UPLOAD_DIR", default="/app/data/cipa/pdfs"
    )
    CIPA_SIGNATURE_MAX_BYTES: int = int(
        _get_env("CIPA_SIGNATURE_MAX_BYTES", default=str(3 * 1024 * 1024)) or str(3 * 1024 * 1024)
    )
    CIPA_ATTACHMENT_MAX_BYTES: int = int(
        _get_env("CIPA_ATTACHMENT_MAX_BYTES", default=str(15 * 1024 * 1024)) or str(15 * 1024 * 1024)
    )
    CIPA_PORTAL_NOTIFICATIONS_ENABLED: bool = (
        str(_get_env("CIPA_PORTAL_NOTIFICATIONS_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )


settings = Settings()
