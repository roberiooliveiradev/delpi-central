from __future__ import annotations

import argparse
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

SI_SCHEMA_NAME = "strategic_indicators"
MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "migrations"


class MigrationError(RuntimeError):
    """Erro de execução de migrations do Strategic Indicators."""


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
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SI_SCHEMA_NAME}";')
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{SI_SCHEMA_NAME}".schema_migrations (
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
        path
        for path in MIGRATIONS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".sql" and path.name.startswith("V")
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_applied_migrations(conn: Any) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT version, name, checksum, executed_at
            FROM "{SI_SCHEMA_NAME}".schema_migrations
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
                f"""
                INSERT INTO "{SI_SCHEMA_NAME}".schema_migrations (version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (version, name, checksum),
            )
        conn.commit()
        print(f"   OK: {path.name}")
    except Exception as exc:
        conn.rollback()
        raise MigrationError(f"Falha ao aplicar migration {path.name}: {exc}") from exc


def find_checksum_mismatches(
    conn: Any, files: list[Path]
) -> list[tuple[str, str, str, str]]:
    """Retorna (version, name, checksum_aplicado, checksum_atual) para divergências."""
    applied = get_applied_migrations(conn)
    mismatches: list[tuple[str, str, str, str]] = []

    for path in files:
        version, name = parse_version_and_name(path)
        checksum = calculate_checksum(path)

        if version not in applied:
            continue

        applied_checksum = applied[version]["checksum"]
        if checksum != applied_checksum:
            mismatches.append((version, name, applied_checksum, checksum))

    return mismatches


def repair_checksum_mismatches(conn: Any, files: list[Path]) -> list[str]:
    """Atualiza checksums registrados para bater com o arquivo no disco.

    Use quando a migration já foi aplicada e o SQL no repositório foi tornado
    idempotente (sem mudança de schema pendente). Não reexecuta o SQL.
    """
    repaired: list[str] = []

    for version, name, _old, new_checksum in find_checksum_mismatches(conn, files):
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE "{SI_SCHEMA_NAME}".schema_migrations
                SET checksum = %s
                WHERE version = %s
                """,
                (new_checksum, version),
            )
        conn.commit()
        repaired.append(f"{version} ({name})")

    return repaired


def validate_migration_history(conn: Any, files: list[Path]) -> None:
    mismatches = find_checksum_mismatches(conn, files)

    if mismatches:
        labels = ", ".join(f"{version}__{name}.sql" for version, name, *_ in mismatches)
        raise MigrationError(
            f"Checksum divergente para {labels}. "
            f"A migration já aplicada foi alterada no repositório. "
            f"Se o schema já reflete a migration e o SQL atual é só idempotente, "
            f"execute: python3 scripts/run_migrations.py repair-checksums"
        )


def reset_migrations() -> None:
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SET lock_timeout = '5s';")
                cur.execute("SET statement_timeout = '30s';")
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                      AND pid <> pg_backend_pid();
                    """
                )
                cur.execute(f'DROP SCHEMA IF EXISTS "{SI_SCHEMA_NAME}" CASCADE;')

            conn.commit()
            print(f'Schema "{SI_SCHEMA_NAME}" removido com sucesso.')
        except Exception as exc:
            conn.rollback()
            raise MigrationError(
                f'Falha ao remover o schema "{SI_SCHEMA_NAME}": {exc}'
            ) from exc


def run_migrations() -> None:
    files = list_migration_files()

    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)

        applied = get_applied_migrations(conn)
        pending = [
            path
            for path in files
            if parse_version_and_name(path)[0] not in applied
        ]

        if not pending:
            print("[strategic-indicators] Nenhuma migration pendente.")
            return

        print("[strategic-indicators] Executando migrations...")
        for path in pending:
            apply_migration(conn, path)

        print("[strategic-indicators] Migrations aplicadas com sucesso.")


def show_status() -> None:
    files = list_migration_files()

    with get_connection() as conn:
        ensure_migrations_table(conn)
        validate_migration_history(conn, files)

        applied = get_applied_migrations(conn)

        print("Status das migrations do Strategic Indicators:")
        for path in files:
            version, name = parse_version_and_name(path)
            status = "APLICADA" if version in applied else "PENDENTE"
            print(f"- {version} | {name} | {status}")


def repair_checksums() -> None:
    files = list_migration_files()

    with get_connection() as conn:
        ensure_migrations_table(conn)
        repaired = repair_checksum_mismatches(conn, files)

    if not repaired:
        print("[strategic-indicators] Nenhum checksum divergente.")
        return

    print("[strategic-indicators] Checksums reparados:")
    for item in repaired:
        print(f"  - {item}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runner de migrations Postgres do Strategic Indicators API.",
    )
    parser.add_argument(
        "command",
        choices=["up", "status", "reset", "repair-checksums"],
        help=(
            "up: aplica pendentes | status: lista status | reset: remove schema "
            "| repair-checksums: alinha checksums já aplicados com os arquivos atuais"
        ),
    )

    args = parser.parse_args()

    if args.command == "up":
        run_migrations()
        return

    if args.command == "status":
        show_status()
        return

    if args.command == "reset":
        reset_migrations()
        return

    if args.command == "repair-checksums":
        repair_checksums()
        return


if __name__ == "__main__":
    main()
