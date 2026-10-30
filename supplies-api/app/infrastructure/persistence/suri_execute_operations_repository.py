"""Durable idempotency claim store for SURI ``execute`` operations.

Postgres adapter over ``supplies.suri_execute_operations`` (V005). The
UNIQUE (actor_subject, entity, action, idempotency_key) constraint makes
the check-then-act window atomic across processes, workers and restarts:

- ``claim`` inserts the operation row as ``in_progress`` — the first
  caller wins; a same-key caller afterwards reads the existing row and
  is classified as ``replay`` (completed result), ``conflict`` (payload
  fingerprint mismatch) or ``in_progress`` (write still in flight —
  never re-executed, the api-delpi tracker holds the durable verdict).
- ``complete`` records the sanitized operation result for replay.

Only the idempotent request envelope is stored — never ERP payload
values (LGPD). A store failure makes ``claim`` raise; callers must fail
closed (a keyed write is never issued without a successful claim).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

from psycopg.types.json import Jsonb

from app.infrastructure.persistence.migrations_runner import get_connection

ClaimKind = Literal["claimed", "replay", "conflict", "in_progress"]


@dataclass(frozen=True)
class ExecuteClaim:
    kind: ClaimKind
    operation_id: str | None = None
    result: dict[str, Any] | None = None


class PostgresSuriExecuteOperationsRepository:
    """Atomic claim/complete over the durable execute-operations table."""

    def __init__(self, *, ttl: timedelta) -> None:
        self._ttl = ttl

    def claim(
        self,
        *,
        actor_subject: str,
        entity: str,
        action: str,
        idempotency_key: str,
        payload_hash: str,
        correlation_id: str,
    ) -> ExecuteClaim:
        """Claim the key or classify the existing row. Raises on DB error."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO supplies.suri_execute_operations (
                        actor_subject, entity, action, idempotency_key,
                        payload_hash, status, correlation_id, expires_at
                    ) VALUES (%s,%s,%s,%s,%s,'in_progress',%s,NOW() + %s::interval)
                    ON CONFLICT (actor_subject, entity, action, idempotency_key)
                    DO NOTHING
                    RETURNING operation_id
                    """,
                    (
                        actor_subject, entity, action, idempotency_key,
                        payload_hash, correlation_id, self._ttl,
                    ),
                )
                row = cur.fetchone()
                if row:
                    conn.commit()
                    return ExecuteClaim(
                        kind="claimed", operation_id=str(row["operation_id"])
                    )
                cur.execute(
                    """
                    SELECT operation_id, payload_hash, status, result
                    FROM supplies.suri_execute_operations
                    WHERE actor_subject = %s AND entity = %s AND action = %s
                      AND idempotency_key = %s
                    """,
                    (actor_subject, entity, action, idempotency_key),
                )
                existing = cur.fetchone()
                if existing is None:
                    # Row expired+GC'd between ON CONFLICT and SELECT would
                    # have blocked the insert — treat a vanished row as a
                    # fresh claim retry (extremely rare, still safe).
                    conn.rollback()
                    return self.claim(
                        actor_subject=actor_subject,
                        entity=entity,
                        action=action,
                        idempotency_key=idempotency_key,
                        payload_hash=payload_hash,
                        correlation_id=correlation_id,
                    )
                conn.commit()
        if str(existing["payload_hash"]).strip() != payload_hash:
            return ExecuteClaim(kind="conflict")
        if existing["status"] == "completed":
            return ExecuteClaim(
                kind="replay",
                operation_id=str(existing["operation_id"]),
                result=existing["result"],
            )
        return ExecuteClaim(
            kind="in_progress", operation_id=str(existing["operation_id"])
        )

    def complete(self, *, operation_id: str, result: dict[str, Any]) -> None:
        """Record the sanitized operation result for future replays."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE supplies.suri_execute_operations
                    SET status = 'completed', result = %s::jsonb,
                        updated_at = NOW()
                    WHERE operation_id = %s
                    """,
                    (Jsonb(result), operation_id),
                )
            conn.commit()

    def gc_expired(self) -> int:
        """Lazy retention — deletes rows past ``expires_at``."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM supplies.suri_execute_operations
                    WHERE expires_at < NOW()
                    """
                )
                count = cur.rowcount
            conn.commit()
        return count
