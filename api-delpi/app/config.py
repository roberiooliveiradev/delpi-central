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
    # ==========================
    # Core / banco principal
    # ==========================
    DB_HOST: str = _get_env("DB_HOST")
    DB_USER: str = _get_env("DB_USER")
    DB_PASSWORD: str = _get_env("DB_PASSWORD")
    DB_DATABASE: str = _get_env("DB_DATABASE", "DB_NAME")
    DB_PORT: str = _get_env("DB_PORT", default="5432")

    # ==========================
    # API Server
    # ==========================
    PORT: str = _get_env("PORT", "API_DELPI_PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    API_ENV: str = _get_env("API_DELPI_ENV", default="development")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    # ==========================
    # Auth / Keycloak
    # ==========================
    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_ISSUER_INTERNAL: str | None = _get_env("KEYCLOAK_ISSUER_INTERNAL")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    # ==========================
    # URLs públicas / portal
    # ==========================
    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    VITE_KC_REALM: str | None = _get_env("VITE_KC_REALM")
    VITE_KC_CLIENT_ID: str | None = _get_env("VITE_KC_CLIENT_ID")
    VITE_KC_REDIRECT_URI: str | None = _get_env("VITE_KC_REDIRECT_URI")

    # ==========================
    # TOTVS legado
    # ==========================
    TOTVS_DB_HOST: str | None = _get_env("TOTVS_DB_HOST")
    TOTVS_DB_PORT: str = _get_env("TOTVS_DB_PORT", default="1433")
    TOTVS_DB_USER: str | None = _get_env("TOTVS_DB_USER")
    TOTVS_DB_PASSWORD: str | None = _get_env("TOTVS_DB_PASSWORD")
    TOTVS_DB_DATABASE: str | None = _get_env("TOTVS_DB_DATABASE")

    # ==========================
    # Plugins PostgreSQL
    # ==========================
    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    # ==========================
    # Compatibilidade temporária
    # ==========================
    POSTGRES_PLUGINS_DB: str | None = _get_env("POSTGRES_PLUGINS_DB")
    POSTGRES_PLUGINS_USER: str | None = _get_env("POSTGRES_PLUGINS_USER")
    POSTGRES_PLUGINS_PASSWORD: str | None = _get_env("POSTGRES_PLUGINS_PASSWORD")

    # ==========================
    # Configurações do agente
    # ==========================
    AUTO_EXECUTE_API: bool = _get_env("AUTO_EXECUTE_API", default="true").lower() == "true"
    CONFIRM_BEFORE_REQUEST: bool = _get_env("CONFIRM_BEFORE_REQUEST", default="false").lower() == "true"
    SHOW_PAYLOAD_BEFORE_EXECUTE: bool = _get_env("SHOW_PAYLOAD_BEFORE_EXECUTE", default="false").lower() == "true"

    # ==========================
    # Portal RH PostgreSQL
    # ==========================
    PORTAL_RH_DB_HOST: str | None = _get_env("PORTAL_RH_DB_HOST")
    PORTAL_RH_DB_PORT: str = _get_env("PORTAL_RH_DB_PORT", default="5432")
    PORTAL_RH_DB_NAME: str | None = _get_env("PORTAL_RH_DB_NAME")
    PORTAL_RH_DB_USER: str | None = _get_env("PORTAL_RH_DB_USER")
    PORTAL_RH_DB_PASSWORD: str | None = _get_env("PORTAL_RH_DB_PASSWORD")
    PORTAL_RH_DB_CONNECT_TIMEOUT: str = _get_env("PORTAL_RH_DB_CONNECT_TIMEOUT", default="5")
    PORTAL_RH_DB_SSLMODE: str = _get_env("PORTAL_RH_DB_SSLMODE", default="prefer")

    # ==========================
    # Google Sheets
    # ==========================
    GOOGLE_SHEETS_TIMEOUT: str = _get_env("GOOGLE_SHEETS_TIMEOUT", default="10")

    QUALITY_SHEET_ID: str | None = _get_env("QUALITY_SHEET_ID")
    QUALITY_KAIZEN_SHEET_GID: str | None = _get_env("QUALITY_KAIZEN_SHEET_GID")
    QUALITY_AUDIT_5S_SHEET_GID: str | None = _get_env("QUALITY_AUDIT_5S_SHEET_GID")
    AUDIT_5S_NC_UPLOAD_DIR: str = _get_env(
        "AUDIT_5S_NC_UPLOAD_DIR",
        default="/app/data/audit-5s-nc",
    )

    TRANSFORMA_MAIS_SHEET_ID: str | None = _get_env("TRANSFORMA_MAIS_SHEET_ID")
    TRANSFORMA_MAIS_GID_PROCESSOS: str | None = _get_env("TRANSFORMA_MAIS_GID_PROCESSOS")
    TRANSFORMA_MAIS_GID_REVISAO: str | None = _get_env("TRANSFORMA_MAIS_GID_REVISAO")
    TRANSFORMA_MAIS_GID_MEDICOES: str | None = _get_env("TRANSFORMA_MAIS_GID_MEDICOES")
    TRANSFORMA_MAIS_GID_INVESTIMENTOS: str | None = _get_env("TRANSFORMA_MAIS_GID_INVESTIMENTOS")
    TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS: str | None = _get_env("TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS")
    TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS: str | None = _get_env(
        "TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS"
    )
    # postgres = schema transformometro (padrão); sheets = contingência legado
    TRANSFORMA_MAIS_DATA_SOURCE: str = _get_env("TRANSFORMA_MAIS_DATA_SOURCE", default="postgres")

    DIRECT_LABOR_SHEET_ID: str | None = _get_env("DIRECT_LABOR_SHEET_ID")
    DIRECT_LABOR_SHEET_GID: str | None = _get_env("DIRECT_LABOR_SHEET_GID")
    PRODUCTION_COST_SHEET_ID: str | None = _get_env("PRODUCTION_COST_SHEET_ID")
    PRODUCTION_COST_SHEET_GID: str | None = _get_env("PRODUCTION_COST_SHEET_GID")
    DEPRECIATION_SHEET_ID: str | None = _get_env("DEPRECIATION_SHEET_ID")
    DEPRECIATION_SHEET_GID: str | None = _get_env("DEPRECIATION_SHEET_GID")

    FINANCIAL_EBITDA_SHEET_ID: str | None = _get_env("FINANCIAL_EBITDA_SHEET_ID")
    FINANCIAL_EBITDA_SHEET_GID: str | None = _get_env("FINANCIAL_EBITDA_SHEET_GID")
    FINANCIAL_FIXED_COST_SHEET_ID: str | None = _get_env("FINANCIAL_FIXED_COST_SHEET_ID")
    FINANCIAL_FIXED_COST_SHEET_GID: str | None = _get_env("FINANCIAL_FIXED_COST_SHEET_GID")
    FINANCIAL_RECEIVABLES_SHEET_ID: str | None = _get_env("FINANCIAL_RECEIVABLES_SHEET_ID")
    FINANCIAL_RECEIVABLES_SHEET_GID: str | None = _get_env("FINANCIAL_RECEIVABLES_SHEET_GID")

    SUPPLIES_IDD_SHEET_ID: str | None = _get_env("SUPPLIES_IDD_SHEET_ID")
    SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID: str | None = _get_env(
        "SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID"
    )

    # ==========================
    # Core API — rastreamento de uso (backend-only)
    # ==========================
    CORE_API_BASE_URL: str | None = _get_env("CORE_API_BASE_URL", default="http://core-api:8000")
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str | None = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN"
    )
    APP_USAGE_APP_ID: str = _get_env("APP_USAGE_APP_ID", default="api-delpi")
    APP_USAGE_TRACKING_ENABLED: bool = (
        _get_env("APP_USAGE_TRACKING_ENABLED", default="true").lower() == "true"
    )

    # ==========================
    # Cache compartilhado (LMP / estoque)
    # ==========================
    QUERY_CACHE_BACKEND: str = _get_env("QUERY_CACHE_BACKEND", default="memory")
    QUERY_CACHE_TTL_SECONDS: str = _get_env("QUERY_CACHE_TTL_SECONDS", default="300")
    REDIS_URL: str | None = _get_env("REDIS_URL")

    # ==========================
    # Telemetria SQL (console)
    # ==========================
    SQL_TELEMETRY_BACKEND: str = _get_env("SQL_TELEMETRY_BACKEND", default="memory")
    SQL_TELEMETRY_MAX_ENTRIES: str = _get_env("SQL_TELEMETRY_MAX_ENTRIES", default="800")


settings = Settings()