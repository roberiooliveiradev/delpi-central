from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import psycopg

logger = logging.getLogger(__name__)

MIGRATION_FILENAME_RE = re.compile(r"^V(\d+)__(.+)\.sql$")


@dataclass(frozen=True)
class MigrationFile:
    version: int
    name: str
    path: Path
    checksum: str


@dataclass(frozen=True)
class MigrationStatus:
    version: int
    name: str
    applied: bool
    checksum: str | None = None
    applied_checksum: str | None = None
    checksum_mismatch: bool = False


class MigrationRunnerError(RuntimeError):
    pass


class MigrationChecksumMismatchError(MigrationRunnerError):
    pass


def _checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _migrations_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "migrations"


def _discover_migrations() -> list[MigrationFile]:
    migrations_dir = _migrations_dir()
    if not migrations_dir.is_dir():
        raise MigrationRunnerError(f"Migrations directory not found: {migrations_dir}")

    files: list[MigrationFile] = []
    for path in sorted(migrations_dir.glob("V*.sql")):
        match = MIGRATION_FILENAME_RE.match(path.name)
        if not match:
            continue
        content = path.read_text(encoding="utf-8")
        files.append(
            MigrationFile(
                version=int(match.group(1)),
                name=match.group(2),
                path=path,
                checksum=_checksum(content),
            )
        )
    files.sort(key=lambda item: item.version)
    return files


def _ensure_schema_migrations_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS production_pulse")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS production_pulse.schema_migrations (
                version INT PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def _load_applied(conn: psycopg.Connection) -> dict[int, tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT version, name, checksum
            FROM production_pulse.schema_migrations
            ORDER BY version
            """
        )
        rows = cur.fetchall()
    return {row[0]: (row[1], row[2]) for row in rows}


def status(conn: psycopg.Connection) -> list[MigrationStatus]:
    _ensure_schema_migrations_table(conn)
    applied = _load_applied(conn)
    result: list[MigrationStatus] = []
    for migration in _discover_migrations():
        applied_row = applied.get(migration.version)
        if applied_row is None:
            result.append(
                MigrationStatus(
                    version=migration.version,
                    name=migration.name,
                    applied=False,
                    checksum=migration.checksum,
                )
            )
            continue
        applied_name, applied_checksum = applied_row
        result.append(
            MigrationStatus(
                version=migration.version,
                name=migration.name,
                applied=True,
                checksum=migration.checksum,
                applied_checksum=applied_checksum,
                checksum_mismatch=applied_checksum != migration.checksum,
            )
        )
        if applied_name != migration.name:
            logger.warning(
                "Migration V%03d name mismatch: applied=%s file=%s",
                migration.version,
                applied_name,
                migration.name,
            )
    return result


def up(conn: psycopg.Connection) -> list[int]:
    _ensure_schema_migrations_table(conn)
    applied = _load_applied(conn)
    applied_versions: list[int] = []

    for migration in _discover_migrations():
        applied_row = applied.get(migration.version)
        if applied_row is not None:
            _, applied_checksum = applied_row
            if applied_checksum != migration.checksum:
                raise MigrationChecksumMismatchError(
                    f"Checksum divergente na migration V{migration.version:03d} "
                    f"({migration.name}). A migration já aplicada foi alterada."
                )
            continue

        content = migration.path.read_text(encoding="utf-8")
        logger.info("Applying migration V%03d__%s", migration.version, migration.name)
        with conn.cursor() as cur:
            cur.execute(content)
            cur.execute(
                """
                INSERT INTO production_pulse.schema_migrations (version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (migration.version, migration.name, migration.checksum),
            )
        conn.commit()
        applied_versions.append(migration.version)

    return applied_versions
