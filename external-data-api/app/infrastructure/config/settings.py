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

    # Canonical schema — immutable. Migrations V001+ create and populate
    # ``external_data`` literally; making it configurable would let the
    # runner record ``schema_migrations`` in one schema while the DDL
    # lands in another (PROC-0076 R1). Isolation between environments is
    # by database/host (PLUGINS_DB_*), never by schema name.
    EXTERNAL_DATA_SCHEMA = "external_data"
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

    EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED = (
        os.getenv("EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED", "false")
        .strip().lower() in {"1", "true", "yes"}
    )

    # MetalCharts (PROC-0076 R5) — Bearer key lives only in backend env;
    # never logged, never returned in payloads. The feed flag AND the
    # catalog source both default OFF (kill switch until S1 homologation
    # verifies symbols/coverage with a real key).
    METALCHARTS_API_KEY = os.getenv("METALCHARTS_API_KEY", "").strip()
    METALCHARTS_BASE_URL = os.getenv(
        "METALCHARTS_BASE_URL", "https://api.metalcharts.org"
    )
    METALCHARTS_ALLOWED_HOSTS = frozenset(
        h.strip().lower()
        for h in os.getenv(
            "METALCHARTS_ALLOWED_HOSTS", "api.metalcharts.org"
        ).split(",")
        if h.strip()
    )
    METALCHARTS_TIMEOUT_SECONDS = float(
        os.getenv("METALCHARTS_TIMEOUT_SECONDS", "15") or "15"
    )
    # Free-plan allowance is 200 weight/month and 10 weight/minute; the
    # budgets below deliberately reserve headroom for homologation,
    # manual recovery and ops — never the full allowance.
    METALCHARTS_MONTHLY_WEIGHT_BUDGET = int(
        os.getenv("METALCHARTS_MONTHLY_WEIGHT_BUDGET", "160") or "160"
    )
    METALCHARTS_MINUTE_WEIGHT_BUDGET = int(
        os.getenv("METALCHARTS_MINUTE_WEIGHT_BUDGET", "8") or "8"
    )
    METALCHARTS_CACHE_TTL_HOURS = int(
        os.getenv("METALCHARTS_CACHE_TTL_HOURS", "48") or "48"
    )

    # R10 — scheduled ingestion runtime (external-data-scheduler
    # service). Master kill switch; per-feed env flags and the source
    # catalog still gate every run inside the job itself.
    EXTERNAL_DATA_SCHEDULER_ENABLED = (
        os.getenv("EXTERNAL_DATA_SCHEDULER_ENABLED", "false")
        .strip().lower() in {"1", "true", "yes"}
    )
    EXTERNAL_DATA_SCHEDULER_FEEDS = tuple(
        f.strip()
        for f in os.getenv(
            "EXTERNAL_DATA_SCHEDULER_FEEDS", "metals-daily"
        ).split(",")
        if f.strip()
    )
    # Local wall-clock time (container TZ) after which a due feed may
    # run — provisional pending provider publication-time evidence.
    EXTERNAL_DATA_SCHEDULER_RUN_AT = os.getenv(
        "EXTERNAL_DATA_SCHEDULER_RUN_AT", "20:30"
    ).strip()
    EXTERNAL_DATA_SCHEDULER_POLL_SECONDS = int(
        os.getenv("EXTERNAL_DATA_SCHEDULER_POLL_SECONDS", "300") or "300"
    )
    # Minimum days between successful runs per feed; overridable via
    # EXTERNAL_DATA_SCHEDULER_<FEED>_INTERVAL_DAYS (feed uppercased,
    # '-'→'_'). metals-daily defaults to 3 because a daily
    # per-symbol history refresh (5 × weight 2 ≈ 300/month) exceeds
    # the upstream 200/month Free-plan allowance.
    EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS = int(
        os.getenv("EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS", "3") or "3"
    )

    EXTERNAL_DATA_FEED_COMEX_MONTHLY_ENABLED = (
        os.getenv("EXTERNAL_DATA_FEED_COMEX_MONTHLY_ENABLED", "false")
        .strip().lower() in {"1", "true", "yes"}
    )
    EXTERNAL_DATA_FEED_IPP_MONTHLY_ENABLED = (
        os.getenv("EXTERNAL_DATA_FEED_IPP_MONTHLY_ENABLED", "false")
        .strip().lower() in {"1", "true", "yes"}
    )

    # R2 providers — hosts are allowlisted (SSRF guard); the Comex file
    # is a bounded, streamed, checksummed download.
    COMEX_IMPORT_URL_TEMPLATE = os.getenv(
        "COMEX_IMPORT_URL_TEMPLATE",
        "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/"
        "IMP_{year}.csv",
    )
    COMEX_ALLOWED_HOSTS = frozenset(
        h.strip().lower()
        for h in os.getenv(
            "COMEX_ALLOWED_HOSTS", "balanca.economia.gov.br"
        ).split(",")
        if h.strip()
    )
    COMEX_TIMEOUT_SECONDS = float(
        os.getenv("COMEX_TIMEOUT_SECONDS", "120") or "120"
    )
    COMEX_MAX_DOWNLOAD_BYTES = int(
        os.getenv("COMEX_MAX_DOWNLOAD_BYTES", "300000000") or "300000000"
    )
    # Optional CA bundle path for hosts whose chain is not served
    # complete (some gov.br endpoints); unset = system CA store.
    COMEX_CA_BUNDLE = os.getenv("COMEX_CA_BUNDLE", "").strip() or True

    IBGE_SIDRA_BASE_URL = os.getenv(
        "IBGE_SIDRA_BASE_URL", "https://apisidra.ibge.gov.br"
    )
    IBGE_ALLOWED_HOSTS = frozenset(
        h.strip().lower()
        for h in os.getenv(
            "IBGE_ALLOWED_HOSTS", "apisidra.ibge.gov.br"
        ).split(",")
        if h.strip()
    )
    IBGE_TIMEOUT_SECONDS = float(
        os.getenv("IBGE_TIMEOUT_SECONDS", "20") or "20"
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
