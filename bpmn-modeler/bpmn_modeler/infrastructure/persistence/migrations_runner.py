from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

SCHEMA_NAME = "bpmn_modeler"
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DbSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout: int = 5
    sslmode: str = "prefer"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password} "
            f"connect_timeout={self.connect_timeout} sslmode={self.sslmode}"
        )


def _env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise MigrationError(f"Missing required env var: {name}")
    return value


def get_settings() -> DbSettings:
    """Shared plugins_hub credentials — platform convention (PLUGINS_DB_*)."""
    return DbSettings(
        host=_env("PLUGINS_DB_HOST"),
        port=int(_env("PLUGINS_DB_PORT")),
        database=_env("PLUGINS_DB_NAME"),
        user=_env("PLUGINS_DB_USER"),
        password=_env("PLUGINS_DB_PASSWORD"),
        connect_timeout=int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5")),
        sslmode=os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer",
    )


def get_connection():
    return psycopg.connect(
        conninfo=get_settings().dsn, row_factory=dict_row, autocommit=False
    )


def ensure_migrations_table(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}";')
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{SCHEMA_NAME}".schema_migrations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    conn.commit()


def list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        raise MigrationError(f"Migrations dir not found: {MIGRATIONS_DIR}")
    files = sorted(
        p for p in MIGRATIONS_DIR.iterdir()
        if p.is_file() and p.suffix == ".sql" and p.name.startswith("V")
    )
    if not files:
        raise MigrationError(f"No migrations found in {MIGRATIONS_DIR}")
    return files


def parse_version_and_name(path: Path) -> tuple[str, str]:
    if "__" not in path.stem:
        raise MigrationError(f"Invalid migration name: {path.name}")
    return tuple(path.stem.split("__", 1))


def checksum_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def applied_migrations(conn: Any) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT version, name, checksum, executed_at "
            f'FROM "{SCHEMA_NAME}".schema_migrations ORDER BY version ASC'
        )
        return {row["version"]: row for row in cur.fetchall()}


def validate_history(conn: Any, files: list[Path]) -> None:
    applied = applied_migrations(conn)
    for path in files:
        version, _ = parse_version_and_name(path)
        if version in applied and checksum_of(path) != applied[version]["checksum"]:
            raise MigrationError(
                f"Checksum divergence for {path.name}; applied migrations are immutable."
            )


def apply_migration(conn: Any, path: Path) -> None:
    version, name = parse_version_and_name(path)
    try:
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
            cur.execute(
                f'INSERT INTO "{SCHEMA_NAME}".schema_migrations (version, name, checksum) '
                "VALUES (%s, %s, %s)",
                (version, name, checksum_of(path)),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise MigrationError(f"Migration {path.name} failed: {exc}") from exc


def run_migrations() -> None:
    files = list_migration_files()
    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_history(conn, files)
        applied = applied_migrations(conn)
        pending = [p for p in files if parse_version_and_name(p)[0] not in applied]
        for path in pending:
            print(f"-> applying {path.name}")
            apply_migration(conn, path)
        print(f"[bpmn-modeler] {len(pending)} migration(s) applied.")


def show_status() -> None:
    files = list_migration_files()
    with get_connection() as conn:
        ensure_migrations_table(conn)
        applied = applied_migrations(conn)
        for path in files:
            version, name = parse_version_and_name(path)
            state = "APPLIED" if version in applied else "PENDING"
            print(f"- {version} | {name} | {state}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BPMN Modeler migration runner")
    parser.add_argument("command", choices=["up", "status"])
    args = parser.parse_args()
    if args.command == "up":
        run_migrations()
    else:
        show_status()


if __name__ == "__main__":
    main()
