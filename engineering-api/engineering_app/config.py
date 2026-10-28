import os

from dotenv import load_dotenv

load_dotenv()


def _get_env(*names: str, default=None):
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


REQUIRED_AUTH_ENVS = ("KEYCLOAK_ISSUER", "KEYCLOAK_AUDIENCE")


class Settings:
    SERVICE_NAME: str = _get_env("SERVICE_NAME", default="engineering-api")
    ENGINEERING_API_ROOT_PATH: str = _get_env(
        "ENGINEERING_API_ROOT_PATH",
        default="/apps/engineering-api",
    )
    PORT: str = _get_env("PORT", default="8000")
    APP_ENV: str = _get_env("APP_ENV", default="production")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    # Superfície de configuração da integração de auth — delpi_auth lê as
    # mesmas envs diretamente; aqui apenas expomos para readiness/boot.
    KEYCLOAK_URL: str = _get_env("KEYCLOAK_URL", default="http://keycloak:8080/auth")
    KEYCLOAK_REALM: str = _get_env("KEYCLOAK_REALM", default="delpi")
    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    CORE_API_URL: str = _get_env(
        "DELPI_AUTH_CORE_API_URL",
        "CORE_API_URL",
        default="http://core-api:8000",
    )
    RBAC_TIMEOUT_SECONDS: str = _get_env(
        "DELPI_AUTH_RBAC_TIMEOUT_SECONDS", default="5.0"
    )
    RBAC_CACHE_TTL_SECONDS: str = _get_env(
        "DELPI_AUTH_RBAC_CACHE_TTL_SECONDS", default="60"
    )
    RBAC_STALE_TTL_SECONDS: str = _get_env(
        "DELPI_AUTH_RBAC_STALE_TTL_SECONDS", default="900"
    )

    # Fontes oficiais consumidas pela Home (delegação com JWT do usuário).
    DELPI_API_URL: str = _get_env("DELPI_API_URL", default="http://delpi-api-delpi:8000")
    REQUESTS_API_URL: str = _get_env("REQUESTS_API_URL", default="http://requests-api:8000")

    # Limites de composição da Home — timeout por fonte, itens por seção e
    # fan-out são limitados por contrato (F2a.S3).
    HOME_SOURCE_TIMEOUT_SECONDS: float = float(
        _get_env("ENGINEERING_HOME_SOURCE_TIMEOUT_SECONDS", default="5.0")
    )
    HOME_MAX_SECTION_ITEMS: int = int(
        _get_env("ENGINEERING_HOME_MAX_SECTION_ITEMS", default="10")
    )
    HOME_MAX_CONCURRENT_SOURCES: int = int(
        _get_env("ENGINEERING_HOME_MAX_CONCURRENT_SOURCES", default="3")
    )

    def resolved_log_level(self) -> int:
        import logging

        return getattr(logging, str(self.LOG_LEVEL).upper(), logging.INFO)

    def missing_auth_envs(self) -> list[str]:
        return [
            name
            for name in REQUIRED_AUTH_ENVS
            if not (os.getenv(name) or "").strip()
        ]


settings = Settings()
