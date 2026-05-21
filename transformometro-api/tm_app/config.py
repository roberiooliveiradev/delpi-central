import os

from dotenv import load_dotenv

from tm_app.infrastructure.providers.google_sheets.sheet_sources import (
    TransformometroSheetSources,
)

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
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="secret")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    TM_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("TM_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
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

    GOOGLE_SHEETS_TIMEOUT: str = _get_env("GOOGLE_SHEETS_TIMEOUT", default="15")
    TRANSFORMA_MAIS_SHEET_ID: str | None = _get_env("TRANSFORMA_MAIS_SHEET_ID")
    TRANSFORMA_MAIS_GID_PROCESSOS: str | None = _get_env("TRANSFORMA_MAIS_GID_PROCESSOS")
    TRANSFORMA_MAIS_GID_REVISAO: str | None = _get_env("TRANSFORMA_MAIS_GID_REVISAO")
    TRANSFORMA_MAIS_GID_MEDICOES: str | None = _get_env("TRANSFORMA_MAIS_GID_MEDICOES")
    TRANSFORMA_MAIS_GID_INVESTIMENTOS: str | None = _get_env(
        "TRANSFORMA_MAIS_GID_INVESTIMENTOS"
    )
    TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS: str | None = _get_env(
        "TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS"
    )
    TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS: str | None = _get_env(
        "TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS"
    )

    def build_sheet_sources(self) -> TransformometroSheetSources:
        sheet_id = self.TRANSFORMA_MAIS_SHEET_ID
        if not sheet_id:
            raise RuntimeError("TRANSFORMA_MAIS_SHEET_ID não configurado.")

        tabs = {
            "processos": self.TRANSFORMA_MAIS_GID_PROCESSOS,
            "revisao": self.TRANSFORMA_MAIS_GID_REVISAO,
            "medicoes": self.TRANSFORMA_MAIS_GID_MEDICOES,
            "investimentos": self.TRANSFORMA_MAIS_GID_INVESTIMENTOS,
            "recursos_compartilhados": self.TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS,
            "revisao_recursos_compartilhados": (
                self.TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS
            ),
        }
        missing = [name for name, gid in tabs.items() if not gid]
        if missing:
            raise RuntimeError(f"GIDs ausentes para abas: {', '.join(missing)}")

        return TransformometroSheetSources(sheet_id=sheet_id, tabs=tabs)  # type: ignore[arg-type]


settings = Settings()
