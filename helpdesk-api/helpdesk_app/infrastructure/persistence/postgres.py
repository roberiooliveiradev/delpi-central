from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from helpdesk_app.domain.models import OAuthSession, PendingAuthorization, StoredResponse
from helpdesk_app.infrastructure.crypto import TokenCipher

SCHEMA = "helpdesk"
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


class MigrationError(RuntimeError):
    pass


def _dsn() -> str:
    return (
        f"host={os.environ['PLUGINS_DB_HOST']} "
        f"port={os.environ.get('PLUGINS_DB_PORT', '5432')} "
        f"dbname={os.environ['PLUGINS_DB_NAME']} "
        f"user={os.environ['PLUGINS_DB_USER']} "
        f"password={os.environ['PLUGINS_DB_PASSWORD']} "
        f"sslmode={os.environ.get('PLUGINS_DB_SSLMODE', 'prefer')}"
    )


def connect():
    return psycopg.connect(_dsn(), row_factory=dict_row, autocommit=False)


def run_migrations() -> None:
    files = sorted(
        path
        for path in MIGRATIONS_DIR.iterdir()
        if path.suffix == ".sql" and path.name.startswith("V")
    )
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";')
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS "{SCHEMA}".schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        conn.commit()
        with conn.cursor() as cur:
            cur.execute(f'SELECT version, checksum FROM "{SCHEMA}".schema_migrations')
            applied = {row["version"]: row["checksum"] for row in cur.fetchall()}
        for path in files:
            version, name = path.stem.split("__", 1)
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            if version in applied:
                if applied[version] != checksum:
                    raise MigrationError(f"Checksum divergente em {path.name}")
                continue
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding="utf-8"))
                cur.execute(
                    f'INSERT INTO "{SCHEMA}".schema_migrations (version, name, checksum) VALUES (%s, %s, %s)',
                    (version, name, checksum),
                )
            conn.commit()


class PostgresStateStore:
    def __init__(self, cipher: TokenCipher, now=None):
        self._cipher = cipher
        self._now = now or (lambda: datetime.now(timezone.utc))

    def save(self, *, state: str, subject: str, code_verifier: str, expires_at) -> None:
        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".oauth_states
                        (state_hash, subject, code_verifier_ciphertext, expires_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (state_hash, subject, self._cipher.encrypt(code_verifier), expires_at),
                )
            conn.commit()

    def consume(self, state: str) -> PendingAuthorization | None:
        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()
        now = self._now()
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE "{SCHEMA}".oauth_states
                    SET consumed_at = %s
                    WHERE state_hash = %s
                      AND consumed_at IS NULL
                      AND expires_at > %s
                    RETURNING subject, code_verifier_ciphertext, expires_at
                    """,
                    (now, state_hash, now),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            return None
        return PendingAuthorization(
            subject=row["subject"],
            code_verifier=self._cipher.decrypt(row["code_verifier_ciphertext"]),
            expires_at=row["expires_at"],
        )


class PostgresSessionStore:
    def __init__(self, cipher: TokenCipher):
        self._cipher = cipher

    def get(self, subject: str) -> OAuthSession | None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT subject, access_token_ciphertext, refresh_token_ciphertext, access_expires_at
                    FROM "{SCHEMA}".oauth_sessions
                    WHERE subject = %s
                    """,
                    (subject,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return OAuthSession(
            subject=row["subject"],
            access_token=self._cipher.decrypt(row["access_token_ciphertext"]),
            refresh_token=self._cipher.decrypt(row["refresh_token_ciphertext"]),
            access_expires_at=row["access_expires_at"],
        )

    def save(self, session: OAuthSession) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".oauth_sessions
                        (subject, access_token_ciphertext, refresh_token_ciphertext, access_expires_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (subject) DO UPDATE SET
                        access_token_ciphertext = EXCLUDED.access_token_ciphertext,
                        refresh_token_ciphertext = EXCLUDED.refresh_token_ciphertext,
                        access_expires_at = EXCLUDED.access_expires_at,
                        updated_at = NOW()
                    """,
                    (
                        session.subject,
                        self._cipher.encrypt(session.access_token),
                        self._cipher.encrypt(session.refresh_token),
                        session.access_expires_at,
                    ),
                )
            conn.commit()

    def delete(self, subject: str) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{SCHEMA}".oauth_sessions WHERE subject = %s',
                    (subject,),
                )
            conn.commit()


class PostgresIdempotencyStore:
    def get(self, subject: str, operation: str, key: str) -> StoredResponse | None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT response_status, response_body
                    FROM "{SCHEMA}".idempotency_keys
                    WHERE subject = %s AND operation = %s AND idempotency_key = %s
                    """,
                    (subject, operation, key),
                )
                row = cur.fetchone()
        if row is None:
            return None
        body = row["response_body"]
        if isinstance(body, str):
            body = json.loads(body)
        return StoredResponse(status_code=row["response_status"], body=body)

    def save(self, subject: str, operation: str, key: str, response: StoredResponse) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".idempotency_keys
                        (subject, operation, idempotency_key, response_status, response_body)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (subject, operation, idempotency_key) DO NOTHING
                    """,
                    (subject, operation, key, response.status_code, Json(response.body)),
                )
            conn.commit()
