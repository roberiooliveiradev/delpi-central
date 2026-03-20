# scripts/run_plugins_migrations.py
from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


ROOT_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT_DIR / "migrations" / "plugins" / "quality"


class MigrationError(RuntimeError):
    """Erro de execução de migrations do contexto plugins."""


@dataclass(frozen=True)
class PluginsDbSettings:
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
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"connect_timeout={self.connect_timeout} "
            f"sslmode={self.sslmode}"
        )


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise MigrationError(f"Variável obrigatória ausente: {name}")
    return value


def get_plugins_db_settings() -> PluginsDbSettings:
    return PluginsDbSettings(
        host=_get_required_env("PLUGINS_DB_HOST"),
        port=int(_get_required_env("PLUGINS_DB_PORT")),
        database=_get_required_env("PLUGINS_DB_NAME"),
        user=_get_required_env("PLUGINS_DB_USER"),
        password=_get_required_env("PLUGINS_DB_PASSWORD"),
        connect_timeout=int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5")),
        sslmode=os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer",
    )


def get_connection():
    settings = get_plugins_db_settings()
    return psycopg.connect(
        conninfo=settings.dsn,
        row_factory=dict_row,
        autocommit=False,
    )


def ensure_migrations_table(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE SCHEMA IF NOT EXISTS quality;

            CREATE TABLE IF NOT EXISTS quality.schema_migrations (
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
        raise MigrationError(f"Pasta de migrations não encontrada: {MIGRATIONS_DIR}")

    files = sorted(
        p for p in MIGRATIONS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == ".sql" and p.name.startswith("V")
    )

    if not files:
        raise MigrationError(f"Nenhuma migration encontrada em: {MIGRATIONS_DIR}")

    return files


def parse_version_and_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "__" not in stem:
        raise MigrationError(
            f"Migration inválida: {path.name}. Use o padrão V001__nome_da_migration.sql"
        )

    version, name = stem.split("__", 1)
    return version, name


def calculate_checksum(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def get_applied_migrations(conn: Any) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT version, name, checksum, executed_at
            FROM quality.schema_migrations
            ORDER BY version ASC
            """
        )
        rows = cur.fetchall()

    return {row["version"]: row for row in rows}


def apply_migration(conn: Any, path: Path) -> None:
    version, name = parse_version_and_name(path)
    checksum = calculate_checksum(path)
    sql = path.read_text(encoding="utf-8")

    print(f"-> Aplicando {path.name}")

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                """
                INSERT INTO quality.schema_migrations (version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (version, name, checksum),
            )
        conn.commit()
        print(f"   OK: {path.name}")
    except Exception as exc:
        conn.rollback()
        raise MigrationError(f"Falha ao aplicar migration {path.name}: {exc}") from exc


def validate_migration_history(conn: Any, files: list[Path]) -> None:
    applied = get_applied_migrations(conn)

    for path in files:
        version, _ = parse_version_and_name(path)
        checksum = calculate_checksum(path)

        if version in applied:
            applied_checksum = applied[version]["checksum"]
            if checksum != applied_checksum:
                raise MigrationError(
                    f"Checksum divergente para {path.name}. "
                    f"A migration já aplicada foi alterada."
                )


def run_migrations() -> None:
    files = list_migration_files()

    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)

        applied = get_applied_migrations(conn)

        pending = []
        for path in files:
            version, _ = parse_version_and_name(path)
            if version not in applied:
                pending.append(path)

        if not pending:
            print("Nenhuma migration pendente.")
            return

        for path in pending:
            apply_migration(conn, path)

        print("Migrations aplicadas com sucesso.")


def show_status() -> None:
    files = list_migration_files()

    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)

        applied = get_applied_migrations(conn)

        print("Status das migrations:")
        for path in files:
            version, name = parse_version_and_name(path)
            status = "APLICADA" if version in applied else "PENDENTE"
            print(f"- {version} | {name} | {status}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runner de migrations do contexto plugins/quality."
    )
    parser.add_argument(
        "command",
        choices=["up", "status"],
        help="up: aplica migrations pendentes | status: mostra status",
    )

    args = parser.parse_args()

    if args.command == "up":
        run_migrations()
        return

    if args.command == "status":
        show_status()
        return


if __name__ == "__main__":
    main()