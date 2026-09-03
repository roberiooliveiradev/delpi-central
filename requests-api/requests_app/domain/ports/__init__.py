from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from requests_app.domain.entities import (
    AssignmentEntry,
    Request,
    RequestType,
    StatusHistoryEntry,
)


class RequestTypeRepositoryPort(ABC):
    @abstractmethod
    def get_by_code(self, code: str) -> RequestType | None: ...

    @abstractmethod
    def get_by_id(self, type_id: UUID | str) -> RequestType | None: ...

    @abstractmethod
    def list_active(self) -> list[RequestType]: ...


class RequestRepositoryPort(ABC):
    @abstractmethod
    def next_request_number(self) -> str: ...

    @abstractmethod
    def create(
        self,
        request: Request,
        *,
        history: StatusHistoryEntry,
    ) -> Request: ...

    @abstractmethod
    def get(self, request_id: UUID | str) -> Request | None: ...

    @abstractmethod
    def update(
        self,
        request: Request,
        *,
        history: StatusHistoryEntry | None = None,
        assignment: AssignmentEntry | None = None,
        expected_version: int | None = None,
    ) -> Request: ...

    @abstractmethod
    def list_mine(
        self,
        *,
        user_id: str,
        type_code: str | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]: ...

    @abstractmethod
    def list_work_queue(
        self,
        *,
        type_codes: list[str] | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        exclude_statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]: ...


class IdempotencyRepositoryPort(ABC):
    @abstractmethod
    def get(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    def save(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        response_snapshot: dict[str, Any],
    ) -> None: ...
