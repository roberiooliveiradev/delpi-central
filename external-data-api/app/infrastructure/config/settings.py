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
