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
    CEC_API_ROOT_PATH: str = _get_env("CEC_API_ROOT_PATH", default="/apps/comite-etica-conduta-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    CEC_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("CEC_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    CORE_API_URL: str = _get_env(
        "DELPI_AUTH_CORE_API_URL", "CORE_API_URL", "CORE_API_BASE_URL", default="http://core-api:8000"
    )
    CORE_API_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        "CORE_API_SERVICE_TOKEN",
        "API_DELPI_INTERNAL_SERVICE_TOKEN",
        default="",
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    CEC_SIGNATURE_UPLOAD_DIR: str = _get_env(
        "CEC_SIGNATURE_UPLOAD_DIR", default="/app/data/comite-etica-conduta/signatures"
    )
    CEC_ATTACHMENT_UPLOAD_DIR: str = _get_env(
        "CEC_ATTACHMENT_UPLOAD_DIR", default="/app/data/comite-etica-conduta/attachments"
    )
    CEC_PDF_UPLOAD_DIR: str = _get_env(
        "CEC_PDF_UPLOAD_DIR", default="/app/data/comite-etica-conduta/pdfs"
    )
    CEC_SIGNATURE_MAX_BYTES: int = int(
        _get_env("CEC_SIGNATURE_MAX_BYTES", default=str(3 * 1024 * 1024)) or str(3 * 1024 * 1024)
    )
    CEC_ATTACHMENT_MAX_BYTES: int = int(
        _get_env("CEC_ATTACHMENT_MAX_BYTES", default=str(15 * 1024 * 1024)) or str(15 * 1024 * 1024)
    )
    CEC_PORTAL_NOTIFICATIONS_ENABLED: bool = (
        str(_get_env("CEC_PORTAL_NOTIFICATIONS_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    CEC_MAIL_ENABLED: bool = (
        str(_get_env("CEC_MAIL_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    # Graph/Outlook — prioriza CEC_*, depois Reports (Minha DELPI), depois canal-denúncia.
    CEC_GRAPH_TENANT_ID: str = _get_env(
        "CEC_GRAPH_TENANT_ID",
        "GRAPH_REPORTS_TENANT_ID",
        "GRAPH_TENANT_ID",
        default="",
    )
    CEC_GRAPH_CLIENT_ID: str = _get_env(
        "CEC_GRAPH_CLIENT_ID",
        "GRAPH_REPORTS_CLIENT_ID",
        "GRAPH_CLIENT_ID",
        default="",
    )
    CEC_GRAPH_CLIENT_SECRET: str = _get_env(
        "CEC_GRAPH_CLIENT_SECRET",
        "GRAPH_REPORTS_CLIENT_SECRET",
        "GRAPH_CLIENT_SECRET",
        default="",
    )
    CEC_GRAPH_MAIL_SENDER: str = _get_env(
        "CEC_GRAPH_MAIL_SENDER",
        "GRAPH_REPORTS_MAIL_SENDER",
        "GRAPH_MAIL_SENDER",
        default="minhadelpi@delpi.com.br",
    )
    CEC_GRAPH_HTTP_TIMEOUT_SECONDS: str = _get_env(
        "CEC_GRAPH_HTTP_TIMEOUT_SECONDS",
        "GRAPH_HTTP_TIMEOUT_SECONDS",
        default="15",
    )


settings = Settings()
