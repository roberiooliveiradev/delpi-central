"""PostgreSQL connection factory — plugins database, external_data schema.

Same PLUGINS_DB_* convention used by the other plugin APIs: the service
connects to the shared plugins PostgreSQL but only ever touches its own
schema (``EXTERNAL_DATA_SCHEMA``, default ``external_data``). Absent
configuration is a first-class state: callers must map it to
``StorageUnavailableError`` rather than guessing a DSN.
"""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from app.application.contracts import StorageUnavailableError
from app.infrastructure.config.settings import Settings


def plugins_dsn() -> str:
    if not Settings.plugins_db_configured():
        raise StorageUnavailableError("plugins database is not configured")
    return (
        f"host={Settings.PLUGINS_DB_HOST} "
        f"port={Settings.PLUGINS_DB_PORT} "
        f"dbname={Settings.PLUGINS_DB_NAME} "
        f"user={Settings.PLUGINS_DB_USER} "
        f"password={Settings.PLUGINS_DB_PASSWORD} "
        f"connect_timeout={Settings.PLUGINS_DB_CONNECT_TIMEOUT} "
        f"sslmode={Settings.PLUGINS_DB_SSLMODE}"
    )


def get_connection():
    """Open a psycopg connection scoped to the external_data schema."""
    conn = psycopg.connect(
        conninfo=plugins_dsn(),
        row_factory=dict_row,
        autocommit=False,
    )
    schema = Settings.EXTERNAL_DATA_SCHEMA
    with conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public;')
    return conn


class StorageProbe:
    """Cheap readiness signal used by read routes and the job."""

    @staticmethod
    def available() -> bool:
        return Settings.plugins_db_configured()
