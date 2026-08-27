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
    CIPA_MAIL_ENABLED: bool = (
        str(_get_env("CIPA_MAIL_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    CIPA_GRAPH_TENANT_ID: str = _get_env(
        "CIPA_GRAPH_TENANT_ID",
        "GRAPH_REPORTS_TENANT_ID",
        "GRAPH_TENANT_ID",
        default="",
    )
    CIPA_GRAPH_CLIENT_ID: str = _get_env(
        "CIPA_GRAPH_CLIENT_ID",
        "GRAPH_REPORTS_CLIENT_ID",
        "GRAPH_CLIENT_ID",
        default="",
    )
    CIPA_GRAPH_CLIENT_SECRET: str = _get_env(
        "CIPA_GRAPH_CLIENT_SECRET",
        "GRAPH_REPORTS_CLIENT_SECRET",
        "GRAPH_CLIENT_SECRET",
        default="",
    )
    CIPA_GRAPH_MAIL_SENDER: str = _get_env(
        "CIPA_GRAPH_MAIL_SENDER",
        "GRAPH_REPORTS_MAIL_SENDER",
        "GRAPH_MAIL_SENDER",
        default="minhadelpi@delpi.com.br",
    )
    CIPA_GRAPH_HTTP_TIMEOUT_SECONDS: str = _get_env(
        "CIPA_GRAPH_HTTP_TIMEOUT_SECONDS",
        "GRAPH_HTTP_TIMEOUT_SECONDS",
        default="15",
    )
    CIPA_ATA_SIGN_INVITE_TTL_DAYS: int = int(
        _get_env("CIPA_ATA_SIGN_INVITE_TTL_DAYS", default="30") or "30"
    )
    CIPA_PUBLIC_SIGN_PATH: str = _get_env(
        "CIPA_PUBLIC_SIGN_PATH", default="/p/cipa/sign"
    )
    CIPA_SIGN_INVITE_MAIL_TRACE_ENABLED: bool = (
        str(
            _get_env("CIPA_SIGN_INVITE_MAIL_TRACE_ENABLED", default="false") or "false"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    CIPA_SIGN_INVITE_MAIL_TRACE_INTERVAL_MINUTES: str = _get_env(
        "CIPA_SIGN_INVITE_MAIL_TRACE_INTERVAL_MINUTES",
        default="15",
    )
    CIPA_SIGN_INVITE_MAIL_TRACE_BATCH_LIMIT: str = _get_env(
        "CIPA_SIGN_INVITE_MAIL_TRACE_BATCH_LIMIT",
        default="50",
    )
    CIPA_SIPAT_QR_DIR: str = _get_env(
        "CIPA_SIPAT_QR_DIR", default="/app/data/cipa/sipat-qr"
    )
    CIPA_PUBLIC_SIPAT_PATH: str = _get_env(
        "CIPA_PUBLIC_SIPAT_PATH", default="/p/cipa/sipat"
    )


settings = Settings()
