# app/infrastructure/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int, *, minimum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    value = int(raw)
    if minimum is not None:
        return max(minimum, value)
    return value


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    CORE_API_INTEGRATIONS_SERVICE_TOKEN = os.getenv(
        "CORE_API_INTEGRATIONS_SERVICE_TOKEN", ""
    ).strip()

    NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED = _env_bool(
        "NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED",
        default=True,
    )
    NOTIFICATIONS_DISPATCH_POLL_SECONDS = _env_int(
        "NOTIFICATIONS_DISPATCH_POLL_SECONDS",
        default=60,
        minimum=15,
    )
    NOTIFICATIONS_DISPATCH_BATCH_LIMIT = min(
        50,
        _env_int(
            "NOTIFICATIONS_DISPATCH_BATCH_LIMIT",
            default=20,
            minimum=1,
        ),
    )

    USER_PRESENCE_ENABLED = _env_bool("USER_PRESENCE_ENABLED", default=True)
    USER_PRESENCE_TTL_SECONDS = _env_int(
        "USER_PRESENCE_TTL_SECONDS",
        default=90,
        minimum=15,
    )
    USER_PRESENCE_STORE = os.getenv("USER_PRESENCE_STORE", "memory").strip().lower()
    REDIS_URL = os.getenv("REDIS_URL", "").strip()

    APP_USAGE_ENABLED = _env_bool("APP_USAGE_ENABLED", default=True)
    APP_USAGE_TTL_SECONDS = _env_int(
        "APP_USAGE_TTL_SECONDS",
        default=90,
        minimum=15,
    )
    APP_USAGE_STORE = os.getenv("APP_USAGE_STORE", "memory").strip().lower()
    APP_USAGE_HISTORY_DAYS = _env_int(
        "APP_USAGE_HISTORY_DAYS",
        default=30,
        minimum=1,
    )

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://delpi:delpi123@postgres-core-test:5432/delpi_core_test"
    )