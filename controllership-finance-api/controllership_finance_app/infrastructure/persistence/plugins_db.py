"""Conexão com o `postgres-plugins` — padrão irmão (supplies/commercial).

Schema isolado `controllership_finance` (CP-D01=A). Conexão por chamada,
credenciais `PLUGINS_DB_*`; ausência de configuração mantém a persistência
desabilitada e as rotas falham fechado com 503.
"""

from __future__ import annotations

import psycopg

from controllership_finance_app.config import settings

SCHEMA_NAME = "controllership_finance"


def plugins_db_configured() -> bool:
    return bool(
        settings.PLUGINS_DB_HOST
        and settings.PLUGINS_DB_NAME
        and settings.PLUGINS_DB_USER
        and settings.PLUGINS_DB_PASSWORD
    )


def plugins_db_connect() -> psycopg.Connection:
    return psycopg.connect(
        host=settings.PLUGINS_DB_HOST,
        port=int(settings.PLUGINS_DB_PORT),
        dbname=settings.PLUGINS_DB_NAME,
        user=settings.PLUGINS_DB_USER,
        password=settings.PLUGINS_DB_PASSWORD,
        connect_timeout=settings.PLUGINS_DB_CONNECT_TIMEOUT,
        sslmode=settings.PLUGINS_DB_SSLMODE,
    )
