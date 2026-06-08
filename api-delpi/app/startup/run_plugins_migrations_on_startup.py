# app/startup/run_plugins_migrations_on_startup.py
from __future__ import annotations

import importlib.util
import logging
import os
import sys
import time
from pathlib import Path

import psycopg

logger = logging.getLogger("api_delpi.plugins_migrations")

_STARTUP_RETRY_ATTEMPTS = int(
    os.getenv("RUN_PLUGINS_MIGRATIONS_STARTUP_RETRIES", "10") or "10"
)
_STARTUP_RETRY_DELAY_SECONDS = float(
    os.getenv("RUN_PLUGINS_MIGRATIONS_STARTUP_RETRY_DELAY", "2") or "2"
)


def _is_enabled() -> bool:
    return (
        str(os.getenv("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", "false") or "false").lower()
        in {"1", "true", "yes", "on"}
    )


def _load_migration_module():
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "run_plugins_migrations.py"

    if not script_path.exists():
        raise RuntimeError(f"Migration script não encontrado: {script_path}")

    spec = importlib.util.spec_from_file_location(
        "run_plugins_migrations", script_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _is_transient_db_error(exc: BaseException) -> bool:
    if isinstance(exc, psycopg.OperationalError):
        return True

    message = str(exc).lower()
    markers = (
        "connection refused",
        "could not connect",
        "connection timed out",
        "server closed the connection",
        "no route to host",
        "name or service not known",
        "operationalerror",
    )
    return any(marker in message for marker in markers)


def run_plugins_migrations_on_startup() -> None:
    if not _is_enabled():
        return

    logger.info("plugins_migrations_startup_begin")
    module = _load_migration_module()
    migration_error = getattr(module, "MigrationError", RuntimeError)

    last_error: BaseException | None = None
    for attempt in range(1, _STARTUP_RETRY_ATTEMPTS + 1):
        try:
            module.run_all_plugins_migrations()
            logger.info("plugins_migrations_startup_done")
            return
        except migration_error as exc:
            last_error = exc
            if attempt < _STARTUP_RETRY_ATTEMPTS and _is_transient_db_error(exc):
                logger.warning(
                    "plugins_migrations_startup_retry attempt=%s/%s error=%s",
                    attempt,
                    _STARTUP_RETRY_ATTEMPTS,
                    exc,
                )
                time.sleep(_STARTUP_RETRY_DELAY_SECONDS)
                continue

            logger.exception("plugins_migrations_startup_failed")
            raise RuntimeError(
                f"Falha ao executar migrations de plugins no startup: {exc}"
            ) from exc

    if last_error is not None:
        raise RuntimeError(
            f"Falha ao executar migrations de plugins no startup: {last_error}"
        ) from last_error
