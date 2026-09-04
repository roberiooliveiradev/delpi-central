"""Postgres repositories for integration outbox and checkpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationCheckpoint,
    IntegrationCheckpointRepositoryPort,
    IntegrationOutboxRepositoryPort,
    IntegrationOutboxRow,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _checkpoint_from_row(row: dict[str, Any] | None) -> IntegrationCheckpoint | None:
    if not row:
        return None
    return IntegrationCheckpoint(
        id=str(row.get("id") or ""),
        source_key=str(row.get("source_key") or ""),
        cursor_value=(str(row["cursor_value"]) if row.get("cursor_value") is not None else None),
        last_success_at=row.get("last_success_at"),
        metadata=_as_dict(row.get("metadata")),
        updated_at=row.get("updated_at"),
    )


def _outbox_from_row(row: dict[str, Any] | None) -> IntegrationOutboxRow | None:
    if not row:
        return None
    return IntegrationOutboxRow(
        id=str(row.get("id") or ""),
        event_type=str(row.get("event_type") or ""),
        aggregate_type=str(row.get("aggregate_type") or ""),
        aggregate_id=str(row.get("aggregate_id") or ""),
        payload=_as_dict(row.get("payload")),
        created_at=row.get("created_at"),
        available_at=row.get("available_at"),
        published_at=row.get("published_at"),
        attempts=int(row.get("attempts") or 0),
        last_error=(str(row["last_error"]) if row.get("last_error") is not None else None),
    )


class PostgresIntegrationCheckpointRepository(
    PluginBaseRepository, IntegrationCheckpointRepositoryPort
):
    def get_by_source_key(self, source_key: str) -> IntegrationCheckpoint | None:
        row = self.fetch_one(
            """
            SELECT
                id::text AS id,
                source_key,
                cursor_value,
                last_success_at,
                metadata,
                updated_at
            FROM commercial.integration_checkpoints
            WHERE source_key = %s
            """,
            (source_key,),
        )
        return _checkpoint_from_row(row)

    def upsert_metadata(
        self,
        *,
        source_key: str,
        metadata: dict[str, Any],
        cursor_value: str | None = None,
        last_success_at: datetime | None = None,
    ) -> IntegrationCheckpoint:
        success_at = last_success_at or datetime.now(timezone.utc)
        row = self.execute_returning_one(
            """
            INSERT INTO commercial.integration_checkpoints (
                source_key, cursor_value, last_success_at, metadata, updated_at
            ) VALUES (%s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (source_key) DO UPDATE SET
                cursor_value = EXCLUDED.cursor_value,
                last_success_at = EXCLUDED.last_success_at,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING
                id::text AS id,
                source_key,
                cursor_value,
                last_success_at,
                metadata,
                updated_at
            """,
            (
                source_key,
                cursor_value,
                success_at,
                json.dumps(metadata or {}),
            ),
        )
        checkpoint = _checkpoint_from_row(row)
        if checkpoint is None:
            raise RuntimeError("integration_checkpoint_upsert_failed")
        return checkpoint


class PostgresIntegrationOutboxRepository(
    PluginBaseRepository, IntegrationOutboxRepositoryPort
):
    def enqueue(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, Any],
    ) -> IntegrationOutboxRow:
        row = self.execute_returning_one(
            """
            INSERT INTO commercial.integration_outbox (
                event_type, aggregate_type, aggregate_id, payload
            ) VALUES (%s, %s, %s, %s::jsonb)
            RETURNING
                id::text AS id,
                event_type,
                aggregate_type,
                aggregate_id,
                payload,
                created_at,
                available_at,
                published_at,
                attempts,
                last_error
            """,
            (
                event_type,
                aggregate_type,
                aggregate_id,
                json.dumps(payload or {}),
            ),
        )
        outbox = _outbox_from_row(row)
        if outbox is None:
            raise RuntimeError("integration_outbox_enqueue_failed")
        return outbox

    def list_pending(self, *, limit: int = 50) -> list[IntegrationOutboxRow]:
        safe_limit = min(200, max(1, int(limit or 50)))
        rows = self.fetch_all(
            """
            SELECT
                id::text AS id,
                event_type,
                aggregate_type,
                aggregate_id,
                payload,
                created_at,
                available_at,
                published_at,
                attempts,
                last_error
            FROM commercial.integration_outbox
            WHERE published_at IS NULL
              AND available_at <= NOW()
            ORDER BY available_at ASC
            LIMIT %s
            """,
            (safe_limit,),
        )
        return [row for row in (_outbox_from_row(item) for item in rows) if row]

    def mark_published(self, outbox_id: str) -> None:
        self.execute(
            """
            UPDATE commercial.integration_outbox
            SET published_at = NOW(), last_error = NULL
            WHERE id = %s::uuid
            """,
            (outbox_id,),
        )

    def mark_failed(
        self,
        outbox_id: str,
        *,
        error: str,
        delay_seconds: int | None = None,
    ) -> None:
        delay = max(1, int(delay_seconds) if delay_seconds is not None else 60)
        self.execute(
            """
            UPDATE commercial.integration_outbox
            SET attempts = attempts + 1,
                last_error = %s,
                available_at = NOW() + make_interval(secs => %s)
            WHERE id = %s::uuid
            """,
            ((error or "")[:2000], delay, outbox_id),
        )

    def defer(self, outbox_id: str, *, delay_seconds: int) -> None:
        delay = max(1, int(delay_seconds))
        self.execute(
            """
            UPDATE commercial.integration_outbox
            SET available_at = NOW() + make_interval(secs => %s)
            WHERE id = %s::uuid
              AND published_at IS NULL
            """,
            (delay, outbox_id),
        )
