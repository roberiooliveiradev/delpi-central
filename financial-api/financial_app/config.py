import os
from datetime import date

from dotenv import load_dotenv

from financial_app.domain.errors import NfeExportConfigurationError
from financial_app.domain.nfe_export import NfeExportSettings

load_dotenv()


def _get_env(*names: str, default=None):
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    FIN_API_ROOT_PATH: str = _get_env("FIN_API_ROOT_PATH", default="/apps/financial-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    FIN_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("FIN_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")
    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")

    DELPI_API_URL: str = _get_env("DELPI_API_URL", default="http://delpi-api-delpi:8000")
    # Prefer FINANCIAL_* so o timeout deste BFF não herda o default curto de outros serviços.
    DELPI_API_TIMEOUT: float = float(
        _get_env("FINANCIAL_DELPI_API_TIMEOUT", "DELPI_API_TIMEOUT", default="90")
    )
    DELPI_API_CALLER_APP: str = _get_env("DELPI_API_CALLER_APP", default="financial-api")

    STRATEGIC_INDICATORS_API_BASE_URL: str = _get_env(
        "STRATEGIC_INDICATORS_API_BASE_URL",
        default="http://strategic-indicators-api:8000",
    )
    STRATEGIC_INDICATORS_API_TIMEOUT: float = float(
        _get_env("STRATEGIC_INDICATORS_API_TIMEOUT", default="30")
    )

    # Questor Zen — token sem default. Ausência não impede o boot da API.
    FIN_QUESTOR_BASE_URL: str = _get_env(
        "FIN_QUESTOR_BASE_URL",
        default="https://alliance.app.questorpublico.com.br",
    )
    FIN_QUESTOR_API_TOKEN: str = _get_env("FIN_QUESTOR_API_TOKEN", default="") or ""
    FIN_QUESTOR_COMPANY_01_ID: str = _get_env("FIN_QUESTOR_COMPANY_01_ID", default="") or ""
    FIN_QUESTOR_COMPANY_02_ID: str = _get_env("FIN_QUESTOR_COMPANY_02_ID", default="") or ""
    FIN_QUESTOR_TIMEOUT_SECONDS: float = float(
        _get_env("FIN_QUESTOR_TIMEOUT_SECONDS", default="30")
    )
    FIN_QUESTOR_DANFE_MAX_BYTES: int = int(
        _get_env("FIN_QUESTOR_DANFE_MAX_BYTES", default="10485760")
    )
    # Exporter de XML NF-e. Permanece desligado até habilitação explícita.
    FIN_QUESTOR_NFE_EXPORT_ENABLED: bool = _env_flag("FIN_QUESTOR_NFE_EXPORT_ENABLED", default=False)
    FIN_QUESTOR_NFE_EXPORT_DIR: str = _get_env("FIN_QUESTOR_NFE_EXPORT_DIR", default="") or ""
    FIN_QUESTOR_NFE_EXPORT_INTERVAL_SECONDS: int = int(
        _get_env("FIN_QUESTOR_NFE_EXPORT_INTERVAL_SECONDS", default="900")
    )
    FIN_QUESTOR_NFE_EXPORT_START_DATE: str = (
        _get_env("FIN_QUESTOR_NFE_EXPORT_START_DATE", default="") or ""
    )
    FIN_QUESTOR_NFE_EXPORT_SCAN_PAGE_SIZE: int = int(
        _get_env("FIN_QUESTOR_NFE_EXPORT_SCAN_PAGE_SIZE", default="100")
    )
    FIN_QUESTOR_NFE_EXPORT_MAX_PAGES: int = int(
        _get_env("FIN_QUESTOR_NFE_EXPORT_MAX_PAGES", default="1000")
    )
    FIN_QUESTOR_NFE_XML_MAX_BYTES: int = int(
        _get_env("FIN_QUESTOR_NFE_XML_MAX_BYTES", default="10485760")
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")


def load_nfe_export_settings() -> NfeExportSettings:
    """Lê o ambiente no momento da chamada. O default de enabled é false."""

    start_raw = (os.getenv("FIN_QUESTOR_NFE_EXPORT_START_DATE") or "").strip()
    start_date = None
    if start_raw:
        try:
            start_date = date.fromisoformat(start_raw)
        except ValueError as exc:
            raise NfeExportConfigurationError(
                "FIN_QUESTOR_NFE_EXPORT_START_DATE inválida."
            ) from exc
    return NfeExportSettings(
        enabled=_env_flag("FIN_QUESTOR_NFE_EXPORT_ENABLED", default=False),
        directory=(os.getenv("FIN_QUESTOR_NFE_EXPORT_DIR") or "").strip(),
        interval_seconds=_bounded_int("FIN_QUESTOR_NFE_EXPORT_INTERVAL_SECONDS", 900),
        start_date=start_date,
        page_size=_bounded_int("FIN_QUESTOR_NFE_EXPORT_SCAN_PAGE_SIZE", 100),
        max_pages=_bounded_int("FIN_QUESTOR_NFE_EXPORT_MAX_PAGES", 1000),
        max_bytes=_bounded_int("FIN_QUESTOR_NFE_XML_MAX_BYTES", 10485760),
    )


def _bounded_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise NfeExportConfigurationError(f"{name} inválida.") from exc


settings = Settings()
