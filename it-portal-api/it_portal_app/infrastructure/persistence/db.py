"""Conexão com o postgres-plugins — schema isolado `it_portal`."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from it_portal_app.config import settings

SCHEMA_NAME = "it_portal"
APPLICATION_NAME = "it-portal-api"


def db_configured() -> bool:
    return bool(
        settings.DB_HOST and settings.DB_NAME and settings.DB_USER and settings.DB_PASSWORD
    )


def db_connect(*, row_factory=dict_row) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        connect_timeout=settings.DB_CONNECT_TIMEOUT,
        sslmode=settings.DB_SSLMODE,
        application_name=APPLICATION_NAME,
        options=f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS}",
        row_factory=row_factory,
    )
