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
    TM_API_ROOT_PATH: str = _get_env("TM_API_ROOT_PATH", default="/apps/transformometro-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    TM_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("TM_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    TM_DASHBOARD_AUTO_RECALC: bool = (
        str(_get_env("TM_DASHBOARD_AUTO_RECALC", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    # Cache de resultado do dashboard em tempo real (fonte única = motor live).
    TM_DASHBOARD_QUERY_CACHE: bool = (
        str(_get_env("TM_DASHBOARD_QUERY_CACHE", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS: int = int(
        _get_env("TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS", default="120") or "120"
    )
    # Manutenção da tabela materializada legada ``dashboard_calculos`` no hook de CRUD.
    # Padrão desligado: o dashboard e o Transforma+ leem do motor live (com query cache).
    TM_DASHBOARD_PERSIST_CACHE: bool = (
        str(_get_env("TM_DASHBOARD_PERSIST_CACHE", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    TM_REVISION_EVIDENCE_UPLOAD_DIR: str = _get_env(
        "TM_REVISION_EVIDENCE_UPLOAD_DIR",
        default="/app/data/revisao-evidencias",
    )
    TM_PROCESSO_ARQUIVO_UPLOAD_DIR: str = _get_env(
        "TM_PROCESSO_ARQUIVO_UPLOAD_DIR",
        default="/app/data/processo-arquivos",
    )
    TM_ATA_SIGNATURE_UPLOAD_DIR: str = _get_env(
        "TM_ATA_SIGNATURE_UPLOAD_DIR",
        default="/app/data/transformometro/atas/signatures",
    )
    TM_ATA_PDF_UPLOAD_DIR: str = _get_env(
        "TM_ATA_PDF_UPLOAD_DIR",
        default="/app/data/transformometro/atas/pdfs",
    )
    TM_ATA_SIGNATURE_MAX_BYTES: int = int(
        _get_env("TM_ATA_SIGNATURE_MAX_BYTES", default=str(2 * 1024 * 1024))
        or str(2 * 1024 * 1024)
    )
    TM_PORTAL_NOTIFICATIONS_ENABLED: bool = (
        str(_get_env("TM_PORTAL_NOTIFICATIONS_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    TM_ATA_SIGN_INVITE_TTL_DAYS: int = int(
        _get_env("TM_ATA_SIGN_INVITE_TTL_DAYS", default="14") or "14"
    )
    TM_MAIL_ENABLED: bool = (
        str(_get_env("TM_MAIL_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    TM_GRAPH_TENANT_ID: str | None = _get_env(
        "TM_GRAPH_TENANT_ID",
        "GRAPH_REPORTS_TENANT_ID",
    )
    TM_GRAPH_CLIENT_ID: str | None = _get_env(
        "TM_GRAPH_CLIENT_ID",
        "GRAPH_REPORTS_CLIENT_ID",
    )
    TM_GRAPH_CLIENT_SECRET: str | None = _get_env(
        "TM_GRAPH_CLIENT_SECRET",
        "GRAPH_REPORTS_CLIENT_SECRET",
    )
    TM_GRAPH_MAIL_SENDER: str | None = _get_env(
        "TM_GRAPH_MAIL_SENDER",
        "GRAPH_REPORTS_MAIL_SENDER",
    )
    TM_GRAPH_HTTP_TIMEOUT_SECONDS: str = _get_env(
        "TM_GRAPH_HTTP_TIMEOUT_SECONDS",
        "GRAPH_HTTP_TIMEOUT_SECONDS",
        default="15",
    )
    TM_SIGN_INVITE_MAIL_TRACE_ENABLED: bool = (
        str(
            _get_env("TM_SIGN_INVITE_MAIL_TRACE_ENABLED", default="false") or "false"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    TM_SIGN_INVITE_MAIL_TRACE_INTERVAL_MINUTES: str = _get_env(
        "TM_SIGN_INVITE_MAIL_TRACE_INTERVAL_MINUTES",
        default="15",
    )
    TM_SIGN_INVITE_MAIL_TRACE_BATCH_LIMIT: str = _get_env(
        "TM_SIGN_INVITE_MAIL_TRACE_BATCH_LIMIT",
        default="50",
    )
    CORE_API_BASE_URL: str = _get_env(
        "CORE_API_BASE_URL",
        default="http://core-api:8000",
    )
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        default="",
    )
    TM_BACKUP_PACKAGE_MAX_BYTES: int = int(
        _get_env("TM_BACKUP_PACKAGE_MAX_BYTES", default=str(500 * 1024 * 1024))
        or str(500 * 1024 * 1024)
    )

    # Kimi / OpenAI-compatible — geração de atas a partir de transcrição.
    # Sem default para a chave: falha clara na primeira chamada se não estiver setada.
    KIMI_API_KEY: str | None = _get_env("KIMI_API_KEY")
    KIMI_BASE_URL: str = _get_env(
        "KIMI_BASE_URL",
        default="https://openrouter.ai/api/v1",
    )
    KIMI_MODEL: str = _get_env("KIMI_MODEL", default="moonshotai/kimi-k3")
    KIMI_TIMEOUT_SECONDS: int = int(
        _get_env("KIMI_TIMEOUT_SECONDS", default="180") or "180"
    )
    KIMI_MAX_TRANSCRIPT_CHARS: int = int(
        _get_env("KIMI_MAX_TRANSCRIPT_CHARS", default="20000") or "20000"
    )
    KIMI_MAX_OUTPUT_TOKENS: int = int(
        _get_env("KIMI_MAX_OUTPUT_TOKENS", default="4096") or "4096"
    )


settings = Settings()
