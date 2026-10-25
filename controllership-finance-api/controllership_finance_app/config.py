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
    CONTROLLERSHIP_FINANCE_API_ROOT_PATH: str = _get_env(
        "CONTROLLERSHIP_FINANCE_API_ROOT_PATH",
        default="/apps/controllership-finance-api",
    )
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    CORE_API_BASE_URL: str = _get_env(
        "CORE_API_BASE_URL",
        "DELPI_AUTH_CORE_API_URL",
        default="http://core-api:8000",
    )
    CORE_API_INTEGRATIONS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
        "CORE_API_SERVICE_TOKEN",
        default="",
    )
    CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN: str = _get_env(
        "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN",
        default="",
    )
    CORE_API_TIMEOUT: str = _get_env("CORE_API_TIMEOUT", default="10")

    # Outbox de notificações do fechamento (R-105-05): poller
    # best-effort recupera eventos EMITTED/FAILED sem nova ação do
    # usuário. Intervalo mínimo efetivo: 15s.
    CF_NOTIFICATION_DISPATCH_ENABLED: str = _get_env(
        "CF_NOTIFICATION_DISPATCH_ENABLED", default="1"
    )
    CF_NOTIFICATION_DISPATCH_INTERVAL_SECONDS: str = _get_env(
        "CF_NOTIFICATION_DISPATCH_INTERVAL_SECONDS", default="60"
    )

    # api-delpi upstream (financial settlement routes, S2S individual).
    DELPI_API_URL: str = _get_env(
        "DELPI_API_URL", default="http://delpi-api-delpi:8000"
    )
    DELPI_API_TIMEOUT_SECONDS: float = float(
        _get_env("DELPI_API_TIMEOUT", default="30")
    )
    DELPI_API_CALLER_APP: str = _get_env(
        "DELPI_API_CALLER_APP", default="controllership-finance-api"
    )

    # Individual S2S credential (client_credentials) — own client, never the
    # supplies credential. Missing values keep the mechanism disabled and the
    # gateway fails closed.
    S2S_TOKEN_URL: str = _get_env("S2S_TOKEN_URL", default="")
    S2S_CLIENT_ID: str = _get_env("S2S_CLIENT_ID", default="")
    S2S_CLIENT_SECRET: str = _get_env("S2S_CLIENT_SECRET", default="")
    S2S_SCOPE: str = _get_env("S2S_SCOPE", default="")
    S2S_TIMEOUT_SECONDS: float = float(
        _get_env("S2S_TIMEOUT_SECONDS", default="10")
    )

    # postgres-plugins — schema próprio `controllership_finance` (CP-D01=A).
    # Valores ausentes mantêm a persistência desabilitada e as rotas de
    # competência falham fechado com 503, nunca com sucesso vazio.
    PLUGINS_DB_HOST: str = _get_env("PLUGINS_DB_HOST", default="")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str = _get_env("PLUGINS_DB_NAME", default="")
    PLUGINS_DB_USER: str = _get_env("PLUGINS_DB_USER", default="")
    PLUGINS_DB_PASSWORD: str = _get_env("PLUGINS_DB_PASSWORD", default="")
    PLUGINS_DB_CONNECT_TIMEOUT: int = int(
        _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    )
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")

    # Binários de evidências P2-Upload: volume persistente dedicado
    # (${DELPI_DATA_HOST_DIR}/cf-closing-documents nos composes).
    CF_DOCUMENT_UPLOAD_DIR: str = _get_env(
        "CF_DOCUMENT_UPLOAD_DIR",
        default="/app/data/cf-closing-documents",
    )

    RUN_MIGRATIONS_ON_STARTUP: bool = _get_env(
        "CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP",
        default="false",
    ).lower() in ("1", "true", "yes")


settings = Settings()

# Configuração obrigatória para readiness do slice IMP-F0 (somente rotas
# públicas hoje; estes itens são pré-requisitos das futuras rotas
# autenticadas e da integração S2S com o Core). Nomes — nunca valores —
# podem aparecer no hint de readiness.
REQUIRED_CONFIG: tuple[str, ...] = (
    "KEYCLOAK_JWKS_URL",
    "KEYCLOAK_ISSUER",
    "KEYCLOAK_AUDIENCE",
    "CORE_API_BASE_URL",
    "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
    "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN",
)


def missing_required_config() -> list[str]:
    return [
        name
        for name in REQUIRED_CONFIG
        if not getattr(settings, name, None)
    ]
