from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class MemoryItemRepositoryPort(ABC):
    @abstractmethod
    def find_active_duplicate(
        self,
        *,
        user_id: UUID | None,
        scope: str,
        type: str,
        content_norm: str,
        project_id: UUID | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        *,
        type: str,
        content: str,
        content_norm: str,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        session_id: UUID | None = None,
        scope: str = "user",
        content_json: dict | None = None,
        confidence: float | None = None,
        source: str = "auto",
        status: str = "active",
        created_by: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def bump_evidence(self, item_id: int, *, confidence: float | None = None) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_active_for_context(
        self,
        *,
        user_id: UUID | None,
        project_id: UUID | None = None,
        limit: int = 20,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_items(
        self,
        *,
        user_id: UUID | None = None,
        scope: str | None = None,
        type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, item_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def set_status(
        self,
        item_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_active_for_reindex(self, *, limit: int = 2000) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        raise NotImplementedError
