# app/infrastructure/providers/totvs/governed_sql_connection.py
"""Fábrica de conexão dedicada para Governed Analytical SQL READ.

Separação de defesa: o caminho governado NUNCA reutiliza o principal
TOTVS_DB_* — exige um principal dedicado (read-only) configurado via
GOVERNED_SQL_DB_*. Sem configuração → fail closed (POLICY_UNAVAILABLE).

Credenciais nunca entram em logs; a application/domain não conhece
credenciais — apenas recebe uma conexão pyodbc.
"""

from __future__ import annotations

import logging
import os
import sys

import pyodbc

from app.config import settings

logger = logging.getLogger("totvs.governed_sql")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setLevel(logging.WARNING)
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)

GOVERNED_SQL_CONNECT_TIMEOUT = int(os.getenv("GOVERNED_SQL_CONNECT_TIMEOUT", "10"))
GOVERNED_SQL_QUERY_TIMEOUT = int(os.getenv("GOVERNED_SQL_QUERY_TIMEOUT", "30"))


def governed_sql_configured() -> bool:
    return bool(
        settings.GOVERNED_SQL_DB_HOST
        and settings.GOVERNED_SQL_DB_DATABASE
        and settings.GOVERNED_SQL_DB_USER
        and settings.GOVERNED_SQL_DB_PASSWORD
    )


def build_governed_sql_connection_string() -> str:
    if not governed_sql_configured():
        raise RuntimeError(
            "GOVERNED_SQL_DB_* não configurado — caminho governed SQL "
            "indisponível."
        )

    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={settings.GOVERNED_SQL_DB_HOST},{settings.GOVERNED_SQL_DB_PORT};"
        f"DATABASE={settings.GOVERNED_SQL_DB_DATABASE};"
        f"UID={settings.GOVERNED_SQL_DB_USER};"
        f"PWD={settings.GOVERNED_SQL_DB_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def create_governed_sql_connection() -> pyodbc.Connection:
    """Abre conexão dedicada para execução governed.

    Falha fechada quando GOVERNED_SQL_DB_* não está configurado —
    nunca cai no principal TOTVS_DB_*.
    """
    connection = pyodbc.connect(
        build_governed_sql_connection_string(),
        timeout=GOVERNED_SQL_CONNECT_TIMEOUT,
    )
    connection.timeout = GOVERNED_SQL_QUERY_TIMEOUT
    return connection
