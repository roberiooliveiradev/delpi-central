"""Runner verify-only do schema lancamento_notas_fiscais (F3 — sem apply)."""

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


class LnfMigrationsVerifyError(RuntimeError):
    """Ledger divergente ou ausente — módulo não sobe (fail-closed)."""


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_versions() -> list[tuple[str, str]]:
    files = sorted(MIGRATIONS_DIR.glob("V*.sql"))
    if len(files) != 14:
        raise LnfMigrationsVerifyError(
            f"esperado 14 arquivos V001–V014 em {MIGRATIONS_DIR}, achados {len(files)}"
        )
    return [(f.stem.split("__", 1)[0], _file_checksum(f)) for f in files]


def verify_lnf_migrations() -> None:
    """Confere presença + checksum no ledger. NÃO executa SQL."""
    expected = _expected_versions()
    host = (settings.PLUGINS_DB_HOST or "").strip()
    if not host:
        raise LnfMigrationsVerifyError("PLUGINS_DB_* ausente — verify LNF impossível")

    dsn = (
        f"host={host} port={settings.PLUGINS_DB_PORT} "
        f"dbname={settings.PLUGINS_DB_NAME} user={settings.PLUGINS_DB_USER} "
        f"password={settings.PLUGINS_DB_PASSWORD} "
        f"connect_timeout={settings.PLUGINS_DB_CONNECT_TIMEOUT} "
        f"sslmode={settings.PLUGINS_DB_SSLMODE}"
    )
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
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
    for version, checksum in expected:
        if version not in rows:
            missing.append(version)
        elif rows[version] != checksum:
            mismatched.append(f"{version} expected={checksum} ledger={rows[version]}")

    if missing or mismatched:
        raise LnfMigrationsVerifyError(
            f"LNF migrations verify FAILED missing={missing} mismatched={mismatched}"
        )
    logger.info("lnf_migrations_verify_ok versions=%s", [v for v, _ in expected])
