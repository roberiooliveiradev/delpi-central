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
    IT_PORTAL_API_ROOT_PATH: str = _get_env(
        "IT_PORTAL_API_ROOT_PATH", default="/apps/it-portal-api"
    )
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    # Mesma URL interna do Core usada pelo delpi_auth; sem URL, atribuir responsavel falha fechado.
    CORE_API_URL: str | None = _get_env("DELPI_AUTH_CORE_API_URL", "CORE_API_BASE_URL")

    # postgres-plugins, schema próprio `it_portal`. IT_PORTAL_DB_USER/PASSWORD
    # permitem uma role dedicada ao domínio; sem elas, vale a credencial
    # PLUGINS_DB_* do cluster. Ausência de configuração mantém as rotas
    # de dados em 503 (fail-closed), nunca com sucesso vazio.
    DB_HOST: str = _get_env("IT_PORTAL_DB_HOST", "PLUGINS_DB_HOST", default="")
    DB_PORT: str = _get_env("IT_PORTAL_DB_PORT", "PLUGINS_DB_PORT", default="5432")
    DB_NAME: str = _get_env("IT_PORTAL_DB_NAME", "PLUGINS_DB_NAME", default="")
    DB_USER: str = _get_env("IT_PORTAL_DB_USER", "PLUGINS_DB_USER", default="")
    DB_PASSWORD: str = _get_env("IT_PORTAL_DB_PASSWORD", "PLUGINS_DB_PASSWORD", default="")
    DB_CONNECT_TIMEOUT: int = int(
        _get_env("IT_PORTAL_DB_CONNECT_TIMEOUT", "PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    )
    DB_SSLMODE: str = _get_env("IT_PORTAL_DB_SSLMODE", "PLUGINS_DB_SSLMODE", default="prefer")
    DB_STATEMENT_TIMEOUT_MS: int = int(
        _get_env("IT_PORTAL_DB_STATEMENT_TIMEOUT_MS", default="10000")
    )

    RUN_MIGRATIONS_ON_STARTUP: bool = _get_env(
        "IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP", default="false"
    ).lower() in ("1", "true", "yes")

    # E4.S1 — ingestão S2S do coletor Linux (fail-closed se vazio na rota).
    S2S_AUDIENCE: str = _get_env("S2S_AUDIENCE", default="")
    S2S_ALLOWED_CLIENTS: str = _get_env("S2S_ALLOWED_CLIENTS", default="")
    IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST: str = _get_env(
        "IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", default=""
    )
    IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS: str = _get_env(
        "IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", default=""
    )

    # G2-S2: nenhuma estacao recebe inventario sem flag + binding S2S exclusivo.
    WORKSTATION_INGEST_ENABLED: bool = _get_env(
        "IT_PORTAL_WORKSTATION_INGEST_ENABLED", default="false"
    ).lower() in ("1", "true", "yes")
    WORKSTATION_COLLECTOR_BINDINGS: str = _get_env(
        "IT_PORTAL_WORKSTATION_COLLECTOR_BINDINGS", default=""
    )
    WORKSTATION_SNAPSHOT_RETENTION: str = _get_env(
        "IT_PORTAL_WORKSTATION_SNAPSHOT_RETENTION", default="50"
    )

    # G2-S4: Keycloak Admin estritamente opt-in, sem conta master reutilizada.
    WORKSTATION_PROVISIONING_ENABLED: bool = _get_env(
        "IT_PORTAL_WORKSTATION_PROVISIONING_ENABLED", default="false"
    ).lower() in ("1", "true", "yes")
    WORKSTATION_KC_ADMIN_URL: str = _get_env("IT_PORTAL_WS_KC_ADMIN_URL", default="")
    WORKSTATION_KC_REALM: str = _get_env("IT_PORTAL_WS_KC_REALM", default="")
    WORKSTATION_KC_PROVISIONER_CLIENT_ID: str = _get_env(
        "IT_PORTAL_WS_KC_PROVISIONER_CLIENT_ID", default=""
    )
    WORKSTATION_KC_PROVISIONER_CLIENT_SECRET: str = _get_env(
        "IT_PORTAL_WS_KC_PROVISIONER_CLIENT_SECRET", default=""
    )


settings = Settings()

REQUIRED_CONFIG: tuple[str, ...] = (
    "KEYCLOAK_JWKS_URL",
    "KEYCLOAK_ISSUER",
    "KEYCLOAK_AUDIENCE",
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)


def missing_required_config() -> list[str]:
    return [name for name in REQUIRED_CONFIG if not getattr(settings, name, None)]
