"""Owner-local idempotency store for GPT commit (pattern from requests-api).

Retention: 24h via query filter (TARGET documented; enforced on get).
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import uuid4

from psycopg.types.json import Jsonb

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection

_SCHEMA = "tv_dashboard"
_OPERATION = "gpt_commit_change"


class IdempotencyConflictError(Exception):
    def __init__(self, message: str = "Idempotency-Key reused with a different request.") -> None:
        super().__init__(message)
        self.message = message


class IdempotencyRepositoryPort(Protocol):
    def get(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = _OPERATION,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None: ...

    def save(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = _OPERATION,
    ) -> None: ...


class InMemoryIdempotencyRepository:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, str, str], dict[str, Any]] = {}

    def get(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = _OPERATION,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None:
        row = self._rows.get((key, operation, actor_user_id))
        if not row:
            return None
        created_at: datetime = row["created_at"]
        if created_at < datetime.now(timezone.utc) - timedelta(hours=max_age_hours):
            return None
        if str(row["request_fingerprint"]) != str(request_fingerprint):
            raise IdempotencyConflictError()
        return deepcopy(row["response_snapshot"])

    def save(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = _OPERATION,
    ) -> None:
        self._rows[(key, operation, actor_user_id)] = {
            "created_at": datetime.now(timezone.utc),
            "request_fingerprint": str(request_fingerprint),
            "response_snapshot": deepcopy(response_snapshot),
            "id": str(uuid4()),
        }


class PostgresIdempotencyRepository:
    def get(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = _OPERATION,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None:
        sql = f"""
        SELECT request_fingerprint, response_snapshot
        FROM {_SCHEMA}.gpt_actions_idempotency_keys
        WHERE key = %s
          AND operation = %s
          AND actor_user_id = %s
          AND created_at >= NOW() - (%s || ' hours')::interval
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (key, operation, actor_user_id, str(max_age_hours)),
                )
                row = cur.fetchone()
        if not row:
            return None
        stored_fp = str(row["request_fingerprint"] or "")
        if stored_fp != str(request_fingerprint):
            raise IdempotencyConflictError()
        snapshot = row["response_snapshot"]
        if isinstance(snapshot, str):
            return json.loads(snapshot)
        return dict(snapshot) if snapshot else None

    def save(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = _OPERATION,
    ) -> None:
        sql = f"""
        INSERT INTO {_SCHEMA}.gpt_actions_idempotency_keys
            (key, operation, actor_user_id, request_fingerprint, response_snapshot)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (key, operation, actor_user_id)
        DO UPDATE SET
            request_fingerprint = EXCLUDED.request_fingerprint,
            response_snapshot = EXCLUDED.response_snapshot,
            created_at = NOW()
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        key,
                        operation,
                        actor_user_id,
                        request_fingerprint,
                        Jsonb(response_snapshot),
                    ),
                )
            conn.commit()
