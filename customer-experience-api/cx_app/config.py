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
    CX_API_ROOT_PATH: str = _get_env("CX_API_ROOT_PATH", default="/apps/customer-experience-api")
    PORT: str = _get_env("PORT", default="8000")
    JWT_SECRET: str = _get_env("JWT_SECRET", "API_DELPI_JWT_SECRET", default="")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")
    CX_RUN_MIGRATIONS_ON_STARTUP: bool = (
        str(_get_env("CX_RUN_MIGRATIONS_ON_STARTUP", default="false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )

    KEYCLOAK_JWKS_URL: str | None = _get_env("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER: str | None = _get_env("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE: str | None = _get_env("KEYCLOAK_AUDIENCE")
    JWT_ALGORITHMS: str = _get_env("JWT_ALGORITHMS", default="RS256")

    # URL pública base usada para montar o link do QR (ex.: https://minhadelpi.com.br).
    PUBLIC_BASE_URL: str | None = _get_env("PUBLIC_BASE_URL")
    VITE_KC_URL: str | None = _get_env("VITE_KC_URL")

    # Caminho público (fora do portal) da página de agradecimento (QR de congratulação).
    CX_PUBLIC_WELCOME_PATH: str = _get_env("CX_PUBLIC_WELCOME_PATH", default="/welcome")
    # Caminho público dos formulários personalizáveis (estilo Google Forms).
    CX_PUBLIC_FORM_PATH: str = _get_env(
        "CX_PUBLIC_FORM_PATH", default="/p/customer-experience/form"
    )

    # Storage persistente (regra persistent-upload-storage.mdc).
    CX_PHOTO_UPLOAD_DIR: str = _get_env(
        "CUSTOMER_EXPERIENCE_PHOTO_UPLOAD_DIR",
        default="/app/data/customer-experience/photos",
    )
    CX_QR_DIR: str = _get_env(
        "CUSTOMER_EXPERIENCE_QR_DIR",
        default="/app/data/customer-experience/qr",
    )
    CX_MAX_PHOTO_BYTES: int = int(_get_env("CX_MAX_PHOTO_BYTES", default=str(10 * 1024 * 1024)))
    CX_FORM_IMAGE_UPLOAD_DIR: str = _get_env(
        "CUSTOMER_EXPERIENCE_FORM_IMAGE_UPLOAD_DIR",
        default="/app/data/customer-experience/form-images",
    )

    PLUGINS_DB_HOST: str | None = _get_env("PLUGINS_DB_HOST")
    PLUGINS_DB_PORT: str = _get_env("PLUGINS_DB_PORT", default="5432")
    PLUGINS_DB_NAME: str | None = _get_env("PLUGINS_DB_NAME")
    PLUGINS_DB_USER: str | None = _get_env("PLUGINS_DB_USER")
    PLUGINS_DB_PASSWORD: str | None = _get_env("PLUGINS_DB_PASSWORD")
    PLUGINS_DB_CONNECT_TIMEOUT: str = _get_env("PLUGINS_DB_CONNECT_TIMEOUT", default="5")
    PLUGINS_DB_SSLMODE: str = _get_env("PLUGINS_DB_SSLMODE", default="prefer")


settings = Settings()
