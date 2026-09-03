from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from requests_app.domain.ports.integration_outbox_port import (
    IntegrationOutboxRepositoryPort,
    IntegrationOutboxRow,
)

_BACKOFF_SECONDS = (30, 120, 600, 3600, 21600)
_MAX_ATTEMPTS = 8


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryIntegrationOutboxRepository(IntegrationOutboxRepositoryPort):
    def __init__(self) -> None:
        self.rows: dict[str, IntegrationOutboxRow] = {}

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
        if dedupe_key:
            for row in self.rows.values():
                if row.dedupe_key == dedupe_key:
                    return deepcopy(row)
        row = IntegrationOutboxRow(
            id=str(uuid4()),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=deepcopy(payload),
            request_id=request_id,
            request_version=request_version,
            dedupe_key=dedupe_key,
            created_at=_utcnow(),
            available_at=_utcnow(),
        )
        self.rows[row.id] = row
        return deepcopy(row)

    def list_pending(self, *, limit: int = 50) -> list[IntegrationOutboxRow]:
        now = _utcnow()
        pending = [
            row
            for row in self.rows.values()
            if row.published_at is None
            and row.dead_letter_at is None
            and (row.next_retry_at is None or row.next_retry_at <= now)
            and (row.available_at is None or row.available_at <= now)
        ]
        pending.sort(key=lambda r: r.created_at or now)
        return [deepcopy(row) for row in pending[:limit]]

    def mark_published(self, outbox_id: str) -> None:
        row = self.rows[outbox_id]
        row.published_at = _utcnow()

    def mark_failed(self, outbox_id: str, *, error: str) -> None:
        row = self.rows[outbox_id]
        row.attempts += 1
        row.last_error = (error or "")[:2000]
        if row.attempts >= _MAX_ATTEMPTS:
            row.dead_letter_at = _utcnow()
            return
        delay = _BACKOFF_SECONDS[min(row.attempts - 1, len(_BACKOFF_SECONDS) - 1)]
        row.next_retry_at = _utcnow() + timedelta(seconds=delay)
