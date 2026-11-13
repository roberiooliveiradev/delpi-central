"""Runner do schema lancamento_notas_fiscais (verify + apply; F6).

Com ledger V001–V014 completo, `apply` é no-op após conferir checksums.
Futuras V015+ são aplicadas aqui (BFF = owner).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.config import settings

logger = logging.getLogger("invoice_posting.migrations")

SCHEMA = "lancamento_notas_fiscais"
MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[3] / "migrations" / "lancamento_notas_fiscais"
)
# Advisory lock key distinct from other plugin runners.
_ADVISORY_LOCK_KEY = 0x4C4E4601  # "LNF\x01"


class LnfMigrationsVerifyError(RuntimeError):
    """Ledger divergente ou ausente — módulo não sobe (fail-closed)."""


class LnfMigrationsApplyError(RuntimeError):
    """Falha ao aplicar migration pendente."""


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _migration_files() -> list[Path]:
    files = sorted(MIGRATIONS_DIR.glob("V*.sql"))
    if not files:
        raise LnfMigrationsVerifyError(
            f"nenhum arquivo V*.sql em {MIGRATIONS_DIR}"
        )
    return files


def _expected_versions() -> list[tuple[str, str, Path]]:
    out: list[tuple[str, str, Path]] = []
    for f in _migration_files():
        version = f.stem.split("__", 1)[0]
        out.append((version, _file_checksum(f), f))
    return out


def _dsn() -> str:
    host = (settings.PLUGINS_DB_HOST or "").strip()
    if not host:
        raise LnfMigrationsVerifyError("PLUGINS_DB_* ausente — LNF migrations impossível")
    return (
        f"host={host} port={settings.PLUGINS_DB_PORT} "
        f"dbname={settings.PLUGINS_DB_NAME} user={settings.PLUGINS_DB_USER} "
        f"password={settings.PLUGINS_DB_PASSWORD} "
        f"connect_timeout={settings.PLUGINS_DB_CONNECT_TIMEOUT} "
        f"sslmode={settings.PLUGINS_DB_SSLMODE}"
    )


def verify_lnf_migrations() -> None:
    """Confere presença + checksum no ledger. NÃO executa SQL."""
    expected = _expected_versions()
    with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT version, checksum
                FROM {SCHEMA}.schema_migrations
                ORDER BY version
                """
            )
            rows = {str(r["version"]): str(r["checksum"]) for r in cur.fetchall()}

    missing = []
    mismatched = []
    for version, checksum, _path in expected:
        if version not in rows:
            missing.append(version)
        elif rows[version] != checksum:
            mismatched.append(f"{version} expected={checksum} ledger={rows[version]}")

    if missing or mismatched:
        raise LnfMigrationsVerifyError(
            f"LNF migrations verify FAILED missing={missing} mismatched={mismatched}"
        )
    logger.info(
        "lnf_migrations_verify_ok versions=%s",
        [v for v, _, _ in expected],
    )


def apply_lnf_migrations() -> list[str]:
    """Aplica V*.sql pendentes; ledger completo → lista vazia (no-op)."""
    expected = _expected_versions()
    applied_names: list[str] = []
    with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (_ADVISORY_LOCK_KEY,))
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT version, checksum
                    FROM {SCHEMA}.schema_migrations
                    ORDER BY version
                    """
                )
                rows = {
                    str(r["version"]): str(r["checksum"]) for r in cur.fetchall()
                }

            for version, checksum, path in expected:
                if version in rows:
                    if rows[version] != checksum:
                        raise LnfMigrationsVerifyError(
                            f"checksum divergente {path.name} "
                            f"expected={checksum} ledger={rows[version]}"
                        )
                    continue

                sql = path.read_text(encoding="utf-8")
                name = path.name
                try:
                    with conn.cursor() as cur:
                        cur.execute("SET lock_timeout = '30s'")
                        cur.execute(sql)
                        cur.execute(
                            f"""
                            INSERT INTO {SCHEMA}.schema_migrations
                                (version, name, checksum)
                            VALUES (%s, %s, %s)
                            """,
                            (version, name, checksum),
                        )
                    conn.commit()
                except psycopg.Error as exc:
                    conn.rollback()
                    raise LnfMigrationsApplyError(
                        f"falha aplicando {name}: {exc}"
                    ) from exc
                applied_names.append(name)
                logger.info("lnf_migration_applied name=%s", name)

            if not applied_names:
                logger.info(
                    "lnf_migrations_apply_noop versions=%s",
                    [v for v, _, _ in expected],
                )
            return applied_names
        finally:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_ADVISORY_LOCK_KEY,))
            conn.commit()
