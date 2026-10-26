"""Typed configuration for external-data-api (X0 §8 freeze).

Provider default is fail-closed (``unavailable``). ``process_local``
rate limiting is only accepted with an explicit single-worker opt-in —
multiworker deployments must use ``distributed`` + healthy ``REDIS_URL``.
S2S validator envs (``S2S_AUDIENCE``, ``S2S_ALLOWED_CLIENTS``,
``KEYCLOAK_*``) are read by ``delpi_auth`` directly.
"""

from __future__ import annotations

import os


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "external-data-api")
    ENV = os.getenv("ENV", "production")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    EXTERNAL_DATA_CNPJ_PROVIDER = os.getenv(
        "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable"
    ).strip().lower()
    BRASILAPI_BASE_URL = os.getenv(
        "BRASILAPI_BASE_URL", "https://brasilapi.com.br/api"
    )
    BRASILAPI_TIMEOUT_SECONDS = float(
        os.getenv("BRASILAPI_TIMEOUT_SECONDS", "6") or "6"
    )

    EXTERNAL_DATA_RATE_LIMIT_STRATEGY = os.getenv(
        "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local"
    ).strip().lower()
    EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED = os.getenv(
        "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", "false"
    ).strip().lower() in ("1", "true", "yes")
    EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE = int(
        os.getenv("EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE", "10") or "10"
    )
    EXTERNAL_DATA_GLOBAL_MAX_QUERIES_PER_MINUTE = int(
        os.getenv("EXTERNAL_DATA_GLOBAL_MAX_QUERIES_PER_MINUTE", "30") or "30"
    )
    EXTERNAL_DATA_RATE_LIMIT_PREFIX = os.getenv(
        "EXTERNAL_DATA_RATE_LIMIT_PREFIX", "external-data:rate-limit:"
    )
    REDIS_URL = os.getenv("REDIS_URL", "").strip()
    EXTERNAL_DATA_REDIS_TIMEOUT_SECONDS = float(
        os.getenv("EXTERNAL_DATA_REDIS_TIMEOUT_SECONDS", "1.5") or "1.5"
    )

    # --- Market data (PROC-0076) -------------------------------------------
    # The service stays functional without a database: market-data routes
    # answer STORAGE_UNAVAILABLE while the CNPJ path keeps working.

    EXTERNAL_DATA_SCHEMA = os.getenv("EXTERNAL_DATA_SCHEMA", "external_data")
    PLUGINS_DB_HOST = os.getenv("PLUGINS_DB_HOST", "").strip()
    PLUGINS_DB_PORT = int(os.getenv("PLUGINS_DB_PORT", "5432") or "5432")
    PLUGINS_DB_NAME = os.getenv("PLUGINS_DB_NAME", "").strip()
    PLUGINS_DB_USER = os.getenv("PLUGINS_DB_USER", "").strip()
    PLUGINS_DB_PASSWORD = os.getenv("PLUGINS_DB_PASSWORD", "")
    PLUGINS_DB_CONNECT_TIMEOUT = int(
        os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5") or "5"
    )
    PLUGINS_DB_SSLMODE = os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer"

    RUN_MIGRATIONS_ON_STARTUP = (
        os.getenv("EXTERNAL_DATA_RUN_MIGRATIONS_ON_STARTUP", "true")
        .strip()
        .lower()
        in {"1", "true", "yes", "on"}
    )

    # Feeds are opt-in per environment; the job also refuses sources that
    # are inactive or unlicensed in the catalog.
    EXTERNAL_DATA_FEED_FX_DAILY_ENABLED = (
        os.getenv("EXTERNAL_DATA_FEED_FX_DAILY_ENABLED", "false").strip().lower()
        in {"1", "true", "yes"}
    )
    EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED = (
        os.getenv("EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED", "false")
        .strip()
        .lower()
        in {"1", "true", "yes"}
    )

    PTAX_BASE_URL = os.getenv(
        "PTAX_BASE_URL",
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1",
    )
    PTAX_TIMEOUT_SECONDS = float(os.getenv("PTAX_TIMEOUT_SECONDS", "15") or "15")

    WORLDBANK_PINKSHEET_MONTHLY_URL = os.getenv(
        "WORLDBANK_PINKSHEET_MONTHLY_URL",
        "https://thedocs.worldbank.org/en/doc/"
        "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
        "CMO-Historical-Data-Monthly.xlsx",
    )
    WORLDBANK_PINKSHEET_TIMEOUT_SECONDS = float(
        os.getenv("WORLDBANK_PINKSHEET_TIMEOUT_SECONDS", "30") or "30"
    )

    EXTERNAL_DATA_USER_AGENT = os.getenv(
        "EXTERNAL_DATA_USER_AGENT", "delpi-external-data-api/1.0"
    )

    @classmethod
    def plugins_db_configured(cls) -> bool:
        return all(
            [
                cls.PLUGINS_DB_HOST,
                cls.PLUGINS_DB_NAME,
                cls.PLUGINS_DB_USER,
                cls.PLUGINS_DB_PASSWORD,
            ]
        )
