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
    # Strategic Indicators API (gateway path)
    # ==========================
    SI_API_ROOT_PATH: str = _get_env("SI_API_ROOT_PATH", default="/apps/strategic-indicators-api")

    # ==========================
    # API Server
    # ==========================
    PORT: str = _get_env("PORT", "STRATEGIC_INDICATORS_API_PORT", "API_DELPI_PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="secret")
    API_ENV: str = _get_env("API_DELPI_ENV", default="development")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    SI_SNAPSHOT_CACHE_TTL_SECONDS: int = int(
        _get_env("SI_SNAPSHOT_CACHE_TTL_SECONDS", default="600") or "600"
    )
    SI_WARMUP_ON_STARTUP: bool = (
        str(_get_env("SI_WARMUP_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )
    SI_WARMUP_TRENDS_MONTHS: int = int(
        _get_env("SI_WARMUP_TRENDS_MONTHS", default="6") or "6"
    )
    SI_PERIOD_SCORES_ENABLED: bool = (
        str(_get_env("SI_PERIOD_SCORES_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERIOD_SCORES_REFRESH_ENABLED: bool = (
        str(_get_env("SI_PERIOD_SCORES_REFRESH_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS: int = int(
        _get_env("SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS", default="300") or "300"
    )
    SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS: int = int(
        _get_env("SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS", default="6") or "6"
    )
    SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT: bool = (
        str(
            _get_env("SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT", default="true") or "true"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERIOD_SCORES_REFRESH_INCLUDE_PREVIOUS: bool = (
        str(
            _get_env("SI_PERIOD_SCORES_REFRESH_INCLUDE_PREVIOUS", default="true") or "true"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERIOD_SCORES_REFRESH_BRANCHES: str = str(
        _get_env("SI_PERIOD_SCORES_REFRESH_BRANCHES", default="") or ""
    )
    SI_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("SI_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

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
    TOTVS_POOL_ENABLED: bool = (
        str(_get_env("TOTVS_POOL_ENABLED", default="true")).lower() in {"1", "true", "yes"}
    )
    TOTVS_POOL_MAX_SIZE: int = int(_get_env("TOTVS_POOL_MAX_SIZE", default="8") or "8")

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

    TRANSFORMA_MAIS_SHEET_ID: str | None = _get_env("TRANSFORMA_MAIS_SHEET_ID")
    TRANSFORMA_MAIS_GID_PROCESSOS: str | None = _get_env("TRANSFORMA_MAIS_GID_PROCESSOS")
    TRANSFORMA_MAIS_GID_REVISAO: str | None = _get_env("TRANSFORMA_MAIS_GID_REVISAO")
    TRANSFORMA_MAIS_GID_MEDICOES: str | None = _get_env("TRANSFORMA_MAIS_GID_MEDICOES")
    TRANSFORMA_MAIS_GID_INVESTIMENTOS: str | None = _get_env("TRANSFORMA_MAIS_GID_INVESTIMENTOS")
    TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS: str | None = _get_env("TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS")
    TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS: str | None = _get_env("TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS")

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

settings = Settings()