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


ROOT_DIR = Path(__file__).resolve().parent.parent
PLUGINS_MIGRATIONS_ROOT = ROOT_DIR / "migrations" / "plugins"


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


def slug_to_schema(plugin_slug: str) -> str:
    schema = plugin_slug.strip().lower().replace("-", "_")
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
        raise MigrationError(
            f"Slug de plugin inválido para schema PostgreSQL: {plugin_slug}"
        )
    return schema


def get_migrations_dir(plugin_slug: str) -> Path:
    return PLUGINS_MIGRATIONS_ROOT / plugin_slug


def ensure_migrations_table(conn: Any, schema_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".schema_migrations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    conn.commit()


def list_migration_files(plugin_slug: str) -> list[Path]:
    migrations_dir = get_migrations_dir(plugin_slug)

    if not migrations_dir.exists():
        raise MigrationError(f"Pasta de migrations não encontrada: {migrations_dir}")

    files = sorted(
        p for p in migrations_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".sql" and p.name.startswith("V")
    )

    if not files:
        raise MigrationError(f"Nenhuma migration encontrada em: {migrations_dir}")

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


def get_applied_migrations(conn: Any, schema_name: str) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT version, name, checksum, executed_at
            FROM "{schema_name}".schema_migrations
            ORDER BY version ASC
            """
        )
        rows = cur.fetchall()

    return {row["version"]: row for row in rows}


def apply_migration(conn: Any, schema_name: str, path: Path) -> None:
    version, name = parse_version_and_name(path)
    checksum = calculate_checksum(path)
    sql = path.read_text(encoding="utf-8")

    print(f"-> Aplicando {path.name}")

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                f"""
                INSERT INTO "{schema_name}".schema_migrations (version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (version, name, checksum),
            )
        conn.commit()
        print(f"   OK: {path.name}")
    except Exception as exc:
        conn.rollback()
        raise MigrationError(f"Falha ao aplicar migration {path.name}: {exc}") from exc


def validate_migration_history(conn: Any, schema_name: str, files: list[Path]) -> None:
    applied = get_applied_migrations(conn, schema_name)

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

def reset_plugin_migrations(plugin_slug: str) -> None:
    schema_name = slug_to_schema(plugin_slug)

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                # Falha rápido se houver lock
                cur.execute("SET lock_timeout = '5s';")
                cur.execute("SET statement_timeout = '30s';")

                # Encerra outras conexões do banco, exceto a atual
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                      AND pid <> pg_backend_pid();
                    """
                )

                cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')

            conn.commit()
            print(f'[{plugin_slug}] Schema "{schema_name}" removido com sucesso.')
        except Exception as exc:
            conn.rollback()
            raise MigrationError(
                f'Falha ao remover o schema "{schema_name}": {exc}'
            ) from exc


def run_plugin_migrations(plugin_slug: str) -> None:
    schema_name = slug_to_schema(plugin_slug)
    files = list_migration_files(plugin_slug)

    with get_connection() as conn:
        ensure_migrations_table(conn, schema_name)
        validate_migration_history(conn, schema_name, files)

        applied = get_applied_migrations(conn, schema_name)
        pending = []

        for path in files:
            version, _ = parse_version_and_name(path)
            if version not in applied:
                pending.append(path)

        if not pending:
            print(f"[{plugin_slug}] Nenhuma migration pendente.")
            return

        print(f"[{plugin_slug}] Executando migrations...")
        for path in pending:
            apply_migration(conn, schema_name, path)

        print(f"[{plugin_slug}] Migrations aplicadas com sucesso.")


def show_plugin_status(plugin_slug: str) -> None:
    schema_name = slug_to_schema(plugin_slug)
    files = list_migration_files(plugin_slug)

    with get_connection() as conn:
        ensure_migrations_table(conn, schema_name)
        validate_migration_history(conn, schema_name, files)

        applied = get_applied_migrations(conn, schema_name)

        print(f"Status das migrations do plugin [{plugin_slug}]:")
        for path in files:
            version, name = parse_version_and_name(path)
            status = "APLICADA" if version in applied else "PENDENTE"
            print(f"- {version} | {name} | {status}")


def list_plugin_slugs() -> list[str]:
    if not PLUGINS_MIGRATIONS_ROOT.exists():
        raise MigrationError(
            f"Pasta raiz de migrations de plugins não encontrada: {PLUGINS_MIGRATIONS_ROOT}"
        )

    slugs = sorted(
        p.name for p in PLUGINS_MIGRATIONS_ROOT.iterdir()
        if p.is_dir()
    )

    if not slugs:
        raise MigrationError(
            f"Nenhum diretório de plugin encontrado em: {PLUGINS_MIGRATIONS_ROOT}"
        )

    return slugs


def run_all_plugins_migrations() -> None:
    for plugin_slug in list_plugin_slugs():
        try:
            run_plugin_migrations(plugin_slug)
        except MigrationError as exc:
            if "Nenhuma migration encontrada" in str(exc):
                print(f"[{plugin_slug}] Sem migrations ainda. Ignorando.")
                continue
            raise


def show_all_plugins_status() -> None:
    for plugin_slug in list_plugin_slugs():
        try:
            show_plugin_status(plugin_slug)
        except MigrationError as exc:
            if "Nenhuma migration encontrada" in str(exc):
                print(f"[{plugin_slug}] Sem migrations ainda. Ignorando.")
                continue
            raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runner de migrations do contexto plugins."
    )
    parser.add_argument(
        "command",
        choices=["up", "status", "reset"],
        help="up: aplica migrations pendentes | status: mostra status | reset: remove o schema do plugin",
    )
    parser.add_argument(
        "--plugin",
        help="Slug do plugin. Ex.: quality, strategic-indicators.",
        default=None,
    )

    args = parser.parse_args()

    if args.command == "up":
        if args.plugin:
            run_plugin_migrations(args.plugin)
        else:
            run_all_plugins_migrations()
        return

    if args.command == "status":
        if args.plugin:
            show_plugin_status(args.plugin)
        else:
            show_all_plugins_status()
        return

    if args.command == "reset":
        if not args.plugin:
            raise MigrationError(
                "O comando reset exige --plugin para evitar remoção acidental de todos os schemas."
            )
        reset_plugin_migrations(args.plugin)
        return


if __name__ == "__main__":
    main()