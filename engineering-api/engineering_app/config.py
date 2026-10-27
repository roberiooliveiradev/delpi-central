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
    SERVICE_NAME: str = _get_env("SERVICE_NAME", default="engineering-api")
    ENGINEERING_API_ROOT_PATH: str = _get_env(
        "ENGINEERING_API_ROOT_PATH",
        default="/apps/engineering-api",
    )
    PORT: str = _get_env("PORT", default="8000")
    APP_ENV: str = _get_env("APP_ENV", default="production")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    def resolved_log_level(self) -> int:
        import logging

        return getattr(logging, str(self.LOG_LEVEL).upper(), logging.INFO)


settings = Settings()
