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
