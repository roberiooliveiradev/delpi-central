"""Read-only SQL Server connection for IntranetDelpi (PARAMETROS_MINHADELPI)."""

from __future__ import annotations

import logging

import pyodbc

from app.config import settings

logger = logging.getLogger("intranet.db")

_CONNECT_TIMEOUT = 10
_QUERY_TIMEOUT = 30


def build_intranet_connection_string() -> str:
    host = settings.INTRANET_DB_HOST or settings.TOTVS_DB_HOST or settings.DB_HOST
    port = settings.INTRANET_DB_PORT or settings.TOTVS_DB_PORT or "1433"
    database = settings.INTRANET_DB_DATABASE
    user = settings.INTRANET_DB_USER or settings.TOTVS_DB_USER or settings.DB_USER
    password = (
        settings.INTRANET_DB_PASSWORD
        or settings.TOTVS_DB_PASSWORD
        or settings.DB_PASSWORD
    )

    if not all([host, database, user, password]):
        raise RuntimeError(
            "Configuração Intranet incompleta. Defina INTRANET_DB_DATABASE e "
            "credenciais INTRANET_DB_* (ou fallback TOTVS_DB_*/DB_*)."
        )

    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def create_intranet_connection() -> pyodbc.Connection:
    connection = pyodbc.connect(
        build_intranet_connection_string(),
        timeout=_CONNECT_TIMEOUT,
    )
    connection.timeout = _QUERY_TIMEOUT
    return connection
