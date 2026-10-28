from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from helpdesk_app.domain.models import (
    IdempotencyClaim,
    OAuthSession,
    PendingAuthorization,
    StoredResponse,
)
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


class PostgresUserTokenStore:
    """Per-user GLPI legacy API tokens (``glpi_users.api_token``), Fernet-encrypted.

    The BFF provisions each user's Remote access key once (REST ``PUT
    /apirest.php/User/{id}`` under the bounded provisioner session) and keeps
    the plaintext here — GLPI stores only the GLPIKey-encrypted copy and never
    returns it on read. This store is what lets later requests open the
    user's own legacy session for writes that must be authored by them.
    """

    def __init__(self, cipher: TokenCipher):
        self._cipher = cipher

    def get(self, glpi_user_id: int) -> str | None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT api_token_ciphertext
                    FROM "{SCHEMA}".glpi_user_tokens
                    WHERE glpi_user_id = %s
                      AND revoked_at IS NULL
                      AND api_token_ciphertext <> ''
                    """,
                    (int(glpi_user_id),),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return self._cipher.decrypt(row["api_token_ciphertext"])

    def save(self, glpi_user_id: int, api_token: str, *, source: str = "provisioned") -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".glpi_user_tokens
                        (glpi_user_id, api_token_ciphertext, source, revoked_at, updated_at)
                    VALUES (%s, %s, %s, NULL, NOW())
                    ON CONFLICT (glpi_user_id) DO UPDATE SET
                        api_token_ciphertext = EXCLUDED.api_token_ciphertext,
                        source = EXCLUDED.source,
                        revoked_at = NULL,
                        updated_at = NOW()
                    """,
                    (int(glpi_user_id), self._cipher.encrypt(api_token), source),
                )
            conn.commit()

    def has_record(self, glpi_user_id: int) -> bool:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 1
                    FROM "{SCHEMA}".glpi_user_tokens
                    WHERE glpi_user_id = %s
                    """,
                    (int(glpi_user_id),),
                )
                return cur.fetchone() is not None

    def is_revoked(self, glpi_user_id: int) -> bool:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 1
                    FROM "{SCHEMA}".glpi_user_tokens
                    WHERE glpi_user_id = %s AND revoked_at IS NOT NULL
                    """,
                    (int(glpi_user_id),),
                )
                return cur.fetchone() is not None

    def adopt(self, glpi_user_id: int) -> None:
        """Authorized-takeover marker: row exists (managed), no usable token.

        Written only by the operator runbook after ownership of a
        pre-existing GLPI Remote access key is established. The next write
        treats the identity as managed and rotates in a governed key.
        """
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".glpi_user_tokens
                        (glpi_user_id, api_token_ciphertext, source, revoked_at, updated_at)
                    VALUES (%s, '', 'adopted', NULL, NOW())
                    ON CONFLICT (glpi_user_id) DO UPDATE SET
                        api_token_ciphertext = '',
                        source = 'adopted',
                        revoked_at = NULL,
                        updated_at = NOW()
                    """,
                    (int(glpi_user_id),),
                )
            conn.commit()

    def revoke(self, glpi_user_id: int) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".glpi_user_tokens
                        (glpi_user_id, api_token_ciphertext, source, revoked_at, updated_at)
                    VALUES (%s, '', 'revoked', NOW(), NOW())
                    ON CONFLICT (glpi_user_id) DO UPDATE SET
                        api_token_ciphertext = '',
                        source = 'revoked',
                        revoked_at = NOW(),
                        updated_at = NOW()
                    """,
                    (int(glpi_user_id),),
                )
            conn.commit()

    def delete(self, glpi_user_id: int) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{SCHEMA}".glpi_user_tokens WHERE glpi_user_id = %s',
                    (int(glpi_user_id),),
                )
            conn.commit()

    @contextmanager
    def provision_lock(self, glpi_user_id: int):
        """Serialize api_token provisioning per user across all instances.

        Postgres advisory lock keyed on this store — two concurrent writes
        for the same user cannot mint competing tokens; the loser re-reads
        the row the winner just saved.
        """
        conn = connect()
        key = f"{SCHEMA}.glpi_user_tokens"
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_lock(hashtextextended(%s, %s))",
                    (key, int(glpi_user_id)),
                )
            yield
        finally:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT pg_advisory_unlock(hashtextextended(%s, %s))",
                        (key, int(glpi_user_id)),
                    )
            finally:
                conn.close()


class PostgresIdempotencyStore:
    def get(self, subject: str, operation: str, key: str) -> StoredResponse | None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT response_status, response_body
                    FROM "{SCHEMA}".idempotency_keys
                    WHERE subject = %s AND operation = %s AND idempotency_key = %s
                      AND state = 'completed'
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

    def claim(
        self,
        subject: str,
        operation: str,
        key: str,
        intent: dict,
    ) -> StoredResponse | IdempotencyClaim | None:
        """Atomically reserve the key BEFORE the external side effect.

        ``INSERT ... ON CONFLICT DO NOTHING`` blocks a concurrent loser
        on the unique index until the winner commits, so exactly one
        caller ever observes the claim. A pre-existing ``in_flight``
        row means a prior execution may have persisted — returned as an
        :class:`IdempotencyClaim` so the caller can fail closed.
        """
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".idempotency_keys
                        (subject, operation, idempotency_key, state, intent, claimed_at)
                    VALUES (%s, %s, %s, 'in_flight', %s, NOW())
                    ON CONFLICT (subject, operation, idempotency_key) DO NOTHING
                    """,
                    (subject, operation, key, Json(intent)),
                )
                if cur.rowcount == 1:
                    conn.commit()
                    return None
                cur.execute(
                    f"""
                    SELECT state, response_status, response_body, intent, claimed_at
                    FROM "{SCHEMA}".idempotency_keys
                    WHERE subject = %s AND operation = %s AND idempotency_key = %s
                    """,
                    (subject, operation, key),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            # Lost the insert race but nothing readable — fail closed as
            # uncertain rather than risk a duplicate side effect.
            return IdempotencyClaim(claimed_at=None, intent=None)
        stored_intent = row["intent"] if isinstance(row["intent"], dict) else None
        if stored_intent != intent:
            # Key reused with a different intent — never replay the
            # stored response (it belongs to another write) and never
            # execute; block for operator review.
            return IdempotencyClaim(
                claimed_at=row["claimed_at"], intent=stored_intent
            )
        if row["state"] == "completed" and row["response_status"] is not None:
            body = row["response_body"]
            if isinstance(body, str):
                body = json.loads(body)
            return StoredResponse(status_code=row["response_status"], body=body)
        return IdempotencyClaim(
            claimed_at=row["claimed_at"],
            intent=row["intent"] if isinstance(row["intent"], dict) else None,
        )

    def save(self, subject: str, operation: str, key: str, response: StoredResponse) -> None:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO "{SCHEMA}".idempotency_keys
                        (subject, operation, idempotency_key, state,
                         response_status, response_body, claimed_at, completed_at)
                    VALUES (%s, %s, %s, 'completed', %s, %s, NOW(), NOW())
                    ON CONFLICT (subject, operation, idempotency_key) DO UPDATE SET
                        state = 'completed',
                        response_status = EXCLUDED.response_status,
                        response_body = EXCLUDED.response_body,
                        completed_at = NOW()
                    """,
                    (subject, operation, key, response.status_code, Json(response.body)),
                )
            conn.commit()

    def release(self, subject: str, operation: str, key: str) -> None:
        """Drop an ``in_flight`` claim — only after a typed rejection
        proves no side effect happened. A completed governed response
        is never released."""
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM "{SCHEMA}".idempotency_keys
                    WHERE subject = %s AND operation = %s AND idempotency_key = %s
                      AND state = 'in_flight'
                    """,
                    (subject, operation, key),
                )
            conn.commit()
