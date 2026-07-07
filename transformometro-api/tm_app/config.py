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
    TM_BACKUP_PACKAGE_MAX_BYTES: int = int(
        _get_env("TM_BACKUP_PACKAGE_MAX_BYTES", default=str(500 * 1024 * 1024))
        or str(500 * 1024 * 1024)
    )


settings = Settings()
