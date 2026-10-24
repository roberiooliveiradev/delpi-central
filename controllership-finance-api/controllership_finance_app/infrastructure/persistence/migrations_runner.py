"""Runner de migrations `controllership_finance` — padrão da plataforma.

- arquivos `migrations/V###__name.sql`, imutáveis após aplicação;
- checksum SHA-256 persistido em `controllership_finance.schema_migrations`;
- cada migration executa dentro de uma transação;
- arquivo já aplicado com checksum divergente aborta (não recria schema).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path

import psycopg

from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

logger = logging.getLogger(__name__)

API_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = Path(
    os.getenv("CONTROLLERSHIP_FINANCE_MIGRATIONS_DIR")
    or API_ROOT / "migrations"
)

_MIGRATION_NAME = re.compile(r"^V(\d+)__(.+)\.sql$")


class MigrationError(RuntimeError):
    pass


def _migration_files() -> list[tuple[int, Path]]:
    if not MIGRATIONS_DIR.is_dir():
        return []
    files: list[tuple[int, Path]] = []
    for path in sorted(MIGRATIONS_DIR.iterdir()):
        match = _MIGRATION_NAME.match(path.name)
        if match:
            files.append((int(match.group(1)), path))
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


def _applied(conn: psycopg.Connection) -> dict[int, str]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT version, checksum FROM {SCHEMA_NAME}.schema_migrations"
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def run_migrations() -> list[str]:
    if not plugins_db_configured():
        logger.warning("plugins_db_not_configured_skip_migrations")
        return []

    applied_names: list[str] = []
    with plugins_db_connect() as conn:
        _ensure_migrations_table(conn)
        applied = _applied(conn)

        for version, path in _migration_files():
            sql = path.read_bytes()
            checksum = hashlib.sha256(sql).hexdigest()

            if version in applied:
                if applied[version] != checksum:
                    raise MigrationError(
                        f"checksum divergente em {path.name} — arquivo "
                        f"aplicado é imutável; criar nova migration"
                    )
                continue

            statement = sql.decode("utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(statement)
                    cur.execute(
                        f"""
                        INSERT INTO {SCHEMA_NAME}.schema_migrations
                            (version, name, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (version, path.name, checksum),
                    )
                conn.commit()
            except psycopg.Error as exc:
                conn.rollback()
                raise MigrationError(
                    f"falha aplicando {path.name}: {exc}"
                ) from exc

            applied_names.append(path.name)
            logger.info("migration_applied name=%s", path.name)

    return applied_names
