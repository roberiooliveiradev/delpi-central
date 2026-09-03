from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class IntegrationOutboxRow:
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    request_id: str | None = None
    request_version: int | None = None
    dedupe_key: str | None = None
    created_at: datetime | None = None
    available_at: datetime | None = None
    published_at: datetime | None = None
    attempts: int = 0
    last_error: str | None = None
    next_retry_at: datetime | None = None
    dead_letter_at: datetime | None = None


class IntegrationOutboxRepositoryPort(ABC):
    @abstractmethod
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
    ) -> IntegrationOutboxRow: ...

    @abstractmethod
    def list_pending(self, *, limit: int = 50) -> list[IntegrationOutboxRow]: ...

    @abstractmethod
    def mark_published(self, outbox_id: str) -> None: ...

    @abstractmethod
    def mark_failed(self, outbox_id: str, *, error: str) -> None: ...
