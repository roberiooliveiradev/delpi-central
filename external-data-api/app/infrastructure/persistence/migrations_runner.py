"""Versioned SQL migrations for the ``external_data`` schema (PROC-0076).

Mirrors the platform migration convention: immutable ``VNNN__name.sql``
files, sha256 checksum recorded per applied version, and a hard fail when
an applied migration's checksum diverges — applied files are never
edited; schema evolution always means a new file.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.plugins_db import get_connection

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


class MigrationError(RuntimeError):
    """Migration execution/validation failure."""


@dataclass(frozen=True)
class MigrationFile:
    path: Path
    version: str
    name: str


def _schema() -> str:
    return Settings.EXTERNAL_DATA_SCHEMA


def list_migration_files() -> list[MigrationFile]:
    if not MIGRATIONS_DIR.exists():
        raise MigrationError(f"migrations directory not found: {MIGRATIONS_DIR}")

    files = sorted(
        path
        for path in MIGRATIONS_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".sql"
        and path.name.startswith("V")
    )
    if not files:
        raise MigrationError(f"no migrations found in: {MIGRATIONS_DIR}")

    return [_parse(path) for path in files]


def _parse(path: Path) -> MigrationFile:
    stem = path.stem
    if "__" not in stem:
        raise MigrationError(
            f"invalid migration name: {path.name}. Expected VNNN__name.sql"
        )
    version, name = stem.split("__", 1)
    return MigrationFile(path=path, version=version, name=name)


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_migrations_table(conn: Any) -> None:
    schema = _schema()
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{schema}".schema_migrations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    conn.commit()


def get_applied_migrations(conn: Any) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT version, name, checksum, executed_at
            FROM "{_schema()}".schema_migrations
            ORDER BY version ASC
            """
        )
        rows = cur.fetchall()
    return {row["version"]: row for row in rows}


def validate_migration_history(conn: Any, files: list[MigrationFile]) -> None:
    applied = get_applied_migrations(conn)
    for migration in files:
        if migration.version in applied:
            checksum = _checksum(migration.path)
            if checksum != applied[migration.version]["checksum"]:
                raise MigrationError(
                    f"checksum mismatch for {migration.path.name}: an applied "
                    "migration file was modified. Applied migrations are "
                    "immutable — create a new migration instead."
                )


def apply_migration(conn: Any, migration: MigrationFile) -> None:
    checksum = _checksum(migration.path)
    sql = migration.path.read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                f"""
                INSERT INTO "{_schema()}".schema_migrations
                    (version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (migration.version, migration.name, checksum),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise MigrationError(
            f"failed to apply migration {migration.path.name}: {exc}"
        ) from exc


def run_migrations() -> list[str]:
    """Apply pending migrations; returns applied versions."""
    files = list_migration_files()
    applied_versions: list[str] = []
    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)
        applied = get_applied_migrations(conn)
        pending = [m for m in files if m.version not in applied]
        for migration in pending:
            apply_migration(conn, migration)
            applied_versions.append(migration.version)
    return applied_versions


def show_status() -> list[tuple[str, str, str]]:
    files = list_migration_files()
    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)
        applied = get_applied_migrations(conn)
    return [
        (m.version, m.name, "applied" if m.version in applied else "pending")
        for m in files
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="external-data-api schema migrations runner."
    )
    parser.add_argument("command", choices=["up", "status"])
    args = parser.parse_args()
    if args.command == "up":
        for version in run_migrations():
            print(f"applied {version}")
        return
    for version, name, status in show_status():
        print(f"{version} | {name} | {status}")


if __name__ == "__main__":
    main()
