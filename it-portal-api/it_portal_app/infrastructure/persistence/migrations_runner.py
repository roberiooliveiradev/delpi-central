"""Runner de migrations `it_portal` — padrão da plataforma.

- arquivos `migrations/V###__name.sql`, imutáveis após aplicação;
- checksum SHA-256 persistido em `it_portal.schema_migrations`;
- cada migration executa dentro de uma transação;
- arquivo já aplicado com checksum divergente aborta o startup.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path

import psycopg
from psycopg.rows import tuple_row

from it_portal_app.infrastructure.persistence.db import (
    SCHEMA_NAME,
    db_configured,
    db_connect,
)

logger = logging.getLogger(__name__)

API_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = Path(os.getenv("IT_PORTAL_MIGRATIONS_DIR") or API_ROOT / "migrations")

_MIGRATION_NAME = re.compile(r"^V(\d+)__(.+)\.sql$")
# Serializa execuções concorrentes (réplicas/restarts simultâneos).
_ADVISORY_LOCK_KEY = 0x17_9047


class MigrationError(RuntimeError):
    pass


def _migration_files() -> list[tuple[int, Path]]:
    if not MIGRATIONS_DIR.is_dir():
        return []
    files = [
        (int(match.group(1)), path)
        for path in MIGRATIONS_DIR.iterdir()
        if (match := _MIGRATION_NAME.match(path.name))
    ]
    files.sort(key=lambda item: item[0])
    return files


def _ensure_migrations_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.schema_migrations (
                version INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum CHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def run_migrations() -> list[str]:
    if not db_configured():
        logger.warning("it_portal_db_not_configured_skip_migrations")
        return []

    applied_names: list[str] = []
    with db_connect(row_factory=tuple_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (_ADVISORY_LOCK_KEY,))
        try:
            _ensure_migrations_table(conn)
            with conn.cursor() as cur:
                cur.execute(f"SELECT version, checksum FROM {SCHEMA_NAME}.schema_migrations")
                applied = {row[0]: row[1] for row in cur.fetchall()}

            for version, path in _migration_files():
                sql = path.read_bytes()
                checksum = hashlib.sha256(sql).hexdigest()
                if version in applied:
                    if applied[version] != checksum:
                        raise MigrationError(
                            f"checksum divergente em {path.name} — migration aplicada "
                            "é imutável; crie uma nova versão"
                        )
                    continue
                try:
                    with conn.cursor() as cur:
                        cur.execute(sql.decode("utf-8"))
                        cur.execute(
                            f"INSERT INTO {SCHEMA_NAME}.schema_migrations "
                            "(version, name, checksum) VALUES (%s, %s, %s)",
                            (version, path.name, checksum),
                        )
                    conn.commit()
                except psycopg.Error as exc:
                    conn.rollback()
                    raise MigrationError(f"falha aplicando {path.name}: {exc}") from exc
                applied_names.append(path.name)
                logger.info("it_portal_migration_applied name=%s", path.name)
        finally:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_ADVISORY_LOCK_KEY,))
            conn.commit()

    return applied_names
