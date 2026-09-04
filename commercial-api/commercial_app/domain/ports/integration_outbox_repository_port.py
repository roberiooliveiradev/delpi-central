"""Ports for commercial integration outbox / checkpoints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class IntegrationCheckpoint:
    id: str
    source_key: str
    cursor_value: str | None
    last_success_at: datetime | None
    metadata: dict[str, Any]
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class IntegrationOutboxRow:
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    created_at: datetime | None
    available_at: datetime | None
    published_at: datetime | None
    attempts: int
    last_error: str | None


class IntegrationCheckpointRepositoryPort(ABC):
    @abstractmethod
    def get_by_source_key(self, source_key: str) -> IntegrationCheckpoint | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_metadata(
        self,
        *,
        source_key: str,
        metadata: dict[str, Any],
        cursor_value: str | None = None,
        last_success_at: datetime | None = None,
    ) -> IntegrationCheckpoint:
        raise NotImplementedError


class IntegrationOutboxRepositoryPort(ABC):
    @abstractmethod
    def enqueue(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, Any],
    ) -> IntegrationOutboxRow:
        raise NotImplementedError

    @abstractmethod
    def list_pending(self, *, limit: int = 50) -> list[IntegrationOutboxRow]:
        raise NotImplementedError

    @abstractmethod
    def mark_published(self, outbox_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_failed(
        self,
        outbox_id: str,
        *,
        error: str,
        delay_seconds: int | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def defer(self, outbox_id: str, *, delay_seconds: int) -> None:
        """Postpone without counting as a failed delivery attempt."""
        raise NotImplementedError
