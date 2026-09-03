from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from psycopg.types.json import Jsonb

from requests_app.domain.ports.integration_outbox_port import (
    IntegrationOutboxRepositoryPort,
    IntegrationOutboxRow,
)
from requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_SCHEMA = "my_requests"
_BACKOFF_SECONDS = (30, 120, 600, 3600, 21600)
_MAX_ATTEMPTS = 8


def _row(data: dict[str, Any]) -> IntegrationOutboxRow:
    payload = data.get("payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return IntegrationOutboxRow(
        id=str(data["id"]),
        event_type=data["event_type"],
        aggregate_type=data["aggregate_type"],
        aggregate_id=data["aggregate_id"],
        payload=payload if isinstance(payload, dict) else {},
        request_id=str(data["request_id"]) if data.get("request_id") else None,
        request_version=data.get("request_version"),
        dedupe_key=data.get("dedupe_key"),
        created_at=data.get("created_at"),
        available_at=data.get("available_at"),
        published_at=data.get("published_at"),
        attempts=int(data.get("attempts") or 0),
        last_error=data.get("last_error"),
        next_retry_at=data.get("next_retry_at"),
        dead_letter_at=data.get("dead_letter_at"),
    )


class PostgresIntegrationOutboxRepository(IntegrationOutboxRepositoryPort):
    def enqueue(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, Any],
        request_id: str | None = None,
        request_version: int | None = None,
        dedupe_key: str | None = None,
    ) -> IntegrationOutboxRow:
        sql = f"""
        INSERT INTO {_SCHEMA}.integration_outbox (
            id, event_type, aggregate_type, aggregate_id, request_id,
            request_version, dedupe_key, payload
        ) VALUES (
            %s::uuid, %s, %s, %s, %s::uuid, %s, %s, %s
        )
        ON CONFLICT (dedupe_key) DO UPDATE SET dedupe_key = EXCLUDED.dedupe_key
        RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(uuid4()),
                        event_type,
                        aggregate_type,
                        aggregate_id,
                        request_id,
                        request_version,
                        dedupe_key,
                        Jsonb(payload),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row(dict(row))

    def list_pending(self, *, limit: int = 50) -> list[IntegrationOutboxRow]:
        sql = f"""
        SELECT * FROM {_SCHEMA}.integration_outbox
        WHERE published_at IS NULL
          AND dead_letter_at IS NULL
          AND available_at <= NOW()
          AND (next_retry_at IS NULL OR next_retry_at <= NOW())
        ORDER BY created_at ASC
        LIMIT %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
        return [_row(dict(row)) for row in rows]

    def mark_published(self, outbox_id: str) -> None:
        sql = f"""
        UPDATE {_SCHEMA}.integration_outbox
        SET published_at = NOW()
        WHERE id = %s::uuid
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (outbox_id,))
            conn.commit()

    def mark_failed(self, outbox_id: str, *, error: str) -> None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT attempts FROM {_SCHEMA}.integration_outbox WHERE id = %s::uuid",
                    (outbox_id,),
                )
                current = cur.fetchone()
                attempts = int((current or {}).get("attempts") or 0) + 1
                if attempts >= _MAX_ATTEMPTS:
                    cur.execute(
                        f"""
                        UPDATE {_SCHEMA}.integration_outbox
                        SET attempts = %s, last_error = %s, dead_letter_at = NOW()
                        WHERE id = %s::uuid
                        """,
                        (attempts, (error or "")[:2000], outbox_id),
                    )
                else:
                    delay = _BACKOFF_SECONDS[min(attempts - 1, len(_BACKOFF_SECONDS) - 1)]
                    cur.execute(
                        f"""
                        UPDATE {_SCHEMA}.integration_outbox
                        SET attempts = %s,
                            last_error = %s,
                            next_retry_at = NOW() + (%s || ' seconds')::interval
                        WHERE id = %s::uuid
                        """,
                        (attempts, (error or "")[:2000], str(delay), outbox_id),
                    )
            conn.commit()
