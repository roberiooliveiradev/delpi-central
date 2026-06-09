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
    # Strategic Indicators API (gateway path)
    # ==========================
    SI_API_ROOT_PATH: str = _get_env("SI_API_ROOT_PATH", default="/apps/strategic-indicators-api")

    # ==========================
    # API Server
    # ==========================
    PORT: str = _get_env("PORT", "STRATEGIC_INDICATORS_API_PORT", "API_DELPI_PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    API_ENV: str = _get_env("API_DELPI_ENV", default="development")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    SI_SNAPSHOT_CACHE_TTL_SECONDS: int = int(
        _get_env("SI_SNAPSHOT_CACHE_TTL_SECONDS", default="600") or "600"
    )
    SI_SERIES_MAX_PARALLEL_PERIODS: int = int(
        _get_env("SI_SERIES_MAX_PARALLEL_PERIODS", default="2") or "2"
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
    SI_PERIOD_SCORES_REFRESH_ON_CONFIG_CHANGE: bool = (
        str(
            _get_env("SI_PERIOD_SCORES_REFRESH_ON_CONFIG_CHANGE", default="true") or "true"
        ).lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS: int = int(
        _get_env("SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS", default="3600") or "3600"
    )
    SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS: int = int(
        _get_env("SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS", default="3") or "3"
    )
    # Desligado por padrão: a leitura para exibição agora usa SEMPRE a base
    # global (scope_department_id="") e filtra o departamento em memória, então
    # materializar uma linha por departamento virou trabalho desnecessário (e
    # pesado). Mantido como flag para diagnósticos pontuais.
    SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT: bool = (
        str(
            _get_env("SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT", default="false")
            or "false"
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
    SI_CALCULATION_SNAPSHOTS_ENABLED: bool = (
        str(_get_env("SI_CALCULATION_SNAPSHOTS_ENABLED", default="true") or "true").lower()
        in {"1", "true", "yes", "on"}
    )
    SI_PERSIST_CALCULATION_SNAPSHOTS_ON_READ: bool = (
        str(
            _get_env("SI_PERSIST_CALCULATION_SNAPSHOTS_ON_READ", default="false") or "false"
        ).lower()
        in {"1", "true", "yes", "on"}
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

settings = Settings()