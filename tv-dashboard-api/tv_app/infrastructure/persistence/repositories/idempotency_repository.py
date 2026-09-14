"""Postgres + in-memory adapters for GPT commit idempotency.

Application owns ``IdempotencyRepositoryPort``; this module only implements it.
"""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from psycopg.types.json import Jsonb

from tv_app.application.ports import IdempotencyAcquireResult, IdempotencyRepositoryPort
from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection

_SCHEMA = "tv_dashboard"
_OPERATION = "gpt_commit_change"


class IdempotencyConflictError(Exception):
    def __init__(self, message: str = "Idempotency-Key reused with a different request.") -> None:
        super().__init__(message)
        self.message = message


class InMemoryIdempotencyRepository:
    """Test double with mutex so concurrent acquire is deterministic."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def acquire(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = _OPERATION,
        max_age_hours: int = 24,
    ) -> IdempotencyAcquireResult:
        with self._lock:
            slot = (key, operation, actor_user_id)
            row = self._rows.get(slot)
            now = datetime.now(timezone.utc)
            if row and row["created_at"] < now - timedelta(hours=max_age_hours):
                del self._rows[slot]
                row = None
            if row is None:
                self._rows[slot] = {
                    "created_at": now,
                    "request_fingerprint": str(request_fingerprint),
                    "status": "in_progress",
                    "response_snapshot": None,
                    "id": str(uuid4()),
                }
                return IdempotencyAcquireResult("ACQUIRED")
            if str(row["request_fingerprint"]) != str(request_fingerprint):
                return IdempotencyAcquireResult("CONFLICT")
            if row["status"] == "completed" and row.get("response_snapshot") is not None:
                return IdempotencyAcquireResult(
                    "REPLAY", deepcopy(row["response_snapshot"])
                )
            return IdempotencyAcquireResult("IN_PROGRESS")

    def complete(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = _OPERATION,
    ) -> None:
        with self._lock:
            slot = (key, operation, actor_user_id)
            row = self._rows.get(slot)
            if not row:
                self._rows[slot] = {
                    "created_at": datetime.now(timezone.utc),
                    "request_fingerprint": str(request_fingerprint),
                    "status": "completed",
                    "response_snapshot": deepcopy(response_snapshot),
                    "id": str(uuid4()),
                }
                return
            if str(row["request_fingerprint"]) != str(request_fingerprint):
                raise IdempotencyConflictError()
            row["status"] = "completed"
            row["response_snapshot"] = deepcopy(response_snapshot)
            row["created_at"] = datetime.now(timezone.utc)


class PostgresIdempotencyRepository:
    def acquire(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = _OPERATION,
        max_age_hours: int = 24,
    ) -> IdempotencyAcquireResult:
        insert_sql = f"""
        INSERT INTO {_SCHEMA}.gpt_actions_idempotency_keys
            (key, operation, actor_user_id, request_fingerprint, response_snapshot, status)
        VALUES (%s, %s, %s, %s, %s::jsonb, 'in_progress')
        ON CONFLICT (key, operation, actor_user_id) DO NOTHING
        RETURNING id
        """
        select_sql = f"""
        SELECT request_fingerprint, response_snapshot, status, created_at
        FROM {_SCHEMA}.gpt_actions_idempotency_keys
        WHERE key = %s
          AND operation = %s
          AND actor_user_id = %s
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (key, operation, actor_user_id, request_fingerprint, "{}"),
                )
                inserted = cur.fetchone()
                if inserted:
                    conn.commit()
                    return IdempotencyAcquireResult("ACQUIRED")
                cur.execute(select_sql, (key, operation, actor_user_id))
                row = cur.fetchone()
                if not row:
                    # Race: deleted between insert miss and select — retry insert once.
                    cur.execute(
                        insert_sql,
                        (key, operation, actor_user_id, request_fingerprint, "{}"),
                    )
                    inserted = cur.fetchone()
                    conn.commit()
                    if inserted:
                        return IdempotencyAcquireResult("ACQUIRED")
                    return IdempotencyAcquireResult("IN_PROGRESS")
                created_at = row["created_at"]
                if isinstance(created_at, datetime):
                    age_ok = created_at >= datetime.now(timezone.utc) - timedelta(
                        hours=max_age_hours
                    )
                else:
                    age_ok = True
                if not age_ok:
                    cur.execute(
                        f"""
                        DELETE FROM {_SCHEMA}.gpt_actions_idempotency_keys
                        WHERE key = %s AND operation = %s AND actor_user_id = %s
                        """,
                        (key, operation, actor_user_id),
                    )
                    cur.execute(
                        insert_sql,
                        (key, operation, actor_user_id, request_fingerprint, "{}"),
                    )
                    inserted = cur.fetchone()
                    conn.commit()
                    if inserted:
                        return IdempotencyAcquireResult("ACQUIRED")
                    return IdempotencyAcquireResult("IN_PROGRESS")
                conn.commit()
                if str(row["request_fingerprint"] or "") != str(request_fingerprint):
                    return IdempotencyAcquireResult("CONFLICT")
                status = str(row.get("status") or "completed")
                if status == "completed":
                    snapshot = row["response_snapshot"]
                    if isinstance(snapshot, str):
                        snapshot = json.loads(snapshot)
                    return IdempotencyAcquireResult(
                        "REPLAY", dict(snapshot) if snapshot else {}
                    )
                return IdempotencyAcquireResult("IN_PROGRESS")

    def complete(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = _OPERATION,
    ) -> None:
        sql = f"""
        UPDATE {_SCHEMA}.gpt_actions_idempotency_keys
        SET response_snapshot = %s,
            status = 'completed',
            created_at = NOW()
        WHERE key = %s
          AND operation = %s
          AND actor_user_id = %s
          AND request_fingerprint = %s
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        Jsonb(response_snapshot),
                        key,
                        operation,
                        actor_user_id,
                        request_fingerprint,
                    ),
                )
                if cur.rowcount == 0:
                    raise IdempotencyConflictError(
                        "Idempotency complete failed: key/fingerprint mismatch."
                    )
            conn.commit()


# Re-export port alias for adapters that still import from this module in tests.
__all__ = [
    "IdempotencyConflictError",
    "IdempotencyRepositoryPort",
    "InMemoryIdempotencyRepository",
    "PostgresIdempotencyRepository",
]
