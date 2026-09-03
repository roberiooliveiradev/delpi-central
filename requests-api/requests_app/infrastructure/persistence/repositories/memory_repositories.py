from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from requests_app.domain.entities import (
    AssignmentEntry,
    Request,
    RequestType,
    StatusHistoryEntry,
)
from requests_app.domain.exceptions import WorkflowEngineError
from requests_app.domain.ports import (
    IdempotencyRepositoryPort,
    RequestRepositoryPort,
    RequestTypeRepositoryPort,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryRequestTypeRepository(RequestTypeRepositoryPort):
    def __init__(self, types: list[RequestType] | None = None) -> None:
        self._by_code: dict[str, RequestType] = {}
        self._by_id: dict[str, RequestType] = {}
        for item in types or []:
            self.save(item)

    def save(self, request_type: RequestType) -> RequestType:
        self._by_code[request_type.code] = request_type
        self._by_id[str(request_type.id)] = request_type
        return request_type

    def get_by_code(self, code: str) -> RequestType | None:
        return self._by_code.get((code or "").strip())

    def get_by_id(self, type_id: UUID | str) -> RequestType | None:
        return self._by_id.get(str(type_id))

    def list_active(self) -> list[RequestType]:
        return [item for item in self._by_code.values() if item.active]


class InMemoryRequestRepository(RequestRepositoryPort):
    def __init__(self) -> None:
        self._requests: dict[str, Request] = {}
        self._history: list[dict[str, Any]] = []
        self._assignments: list[dict[str, Any]] = []
        self._seq = 0

    def next_request_number(self) -> str:
        self._seq += 1
        year = _utcnow().year
        return f"REQ-{year}-{self._seq:06d}"

    def create(self, request: Request, *, history: StatusHistoryEntry) -> Request:
        stored = deepcopy(request)
        now = _utcnow()
        stored.created_at = stored.created_at or now
        stored.updated_at = now
        self._requests[str(stored.id)] = stored
        self._history.append(
            {
                "request_id": str(stored.id),
                "from_status": history.from_status,
                "to_status": history.to_status,
                "action": history.action,
                "actor_user_id": history.actor_user_id,
                "actor_name": history.actor_name,
                "justification": history.justification,
                "changes": deepcopy(history.changes),
            }
        )
        return deepcopy(stored)

    def get(self, request_id: UUID | str) -> Request | None:
        found = self._requests.get(str(request_id))
        return deepcopy(found) if found else None

    def update(
        self,
        request: Request,
        *,
        history: StatusHistoryEntry | None = None,
        assignment: AssignmentEntry | None = None,
        expected_version: int | None = None,
    ) -> Request:
        current = self._requests.get(str(request.id))
        if current is None:
            raise KeyError(str(request.id))
        if expected_version is not None and current.version != expected_version:
            raise WorkflowEngineError(code="stale_version", status_code=409)
        stored = deepcopy(request)
        stored.updated_at = _utcnow()
        self._requests[str(stored.id)] = stored
        if history is not None:
            self._history.append(
                {
                    "request_id": str(stored.id),
                    "from_status": history.from_status,
                    "to_status": history.to_status,
                    "action": history.action,
                    "actor_user_id": history.actor_user_id,
                    "actor_name": history.actor_name,
                    "justification": history.justification,
                    "changes": deepcopy(history.changes),
                }
            )
        if assignment is not None:
            self._assignments.append(
                {
                    "request_id": str(stored.id),
                    "role": assignment.role,
                    "assignee_user_id": assignment.assignee_user_id,
                    "queue_code": assignment.queue_code,
                }
            )
        return deepcopy(stored)

    def list_mine(
        self,
        *,
        user_id: str,
        type_code: str | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]:
        items = [
            item
            for item in self._requests.values()
            if item.created_by_user_id == user_id
            and (not type_code or item.type_code == type_code)
            and (not status or item.status == status)
            and (not branch_code or item.branch_code == branch_code)
        ]
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        total = len(items)
        start = max(page - 1, 0) * page_size
        return [deepcopy(item) for item in items[start : start + page_size]], total

    def list_work_queue(
        self,
        *,
        type_codes: list[str] | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        exclude_statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]:
        excluded = set(exclude_statuses or [])
        allowed_types = set(type_codes) if type_codes is not None else None
        items = []
        for item in self._requests.values():
            if allowed_types is not None and item.type_code not in allowed_types:
                continue
            if status and item.status != status:
                continue
            if branch_code and item.branch_code != branch_code:
                continue
            if item.status in excluded:
                continue
            items.append(item)
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        total = len(items)
        start = max(page - 1, 0) * page_size
        return [deepcopy(item) for item in items[start : start + page_size]], total


class InMemoryIdempotencyRepository(IdempotencyRepositoryPort):
    def __init__(self) -> None:
        self._rows: dict[tuple[str, str, str], dict[str, Any]] = {}

    def get(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None:
        row = self._rows.get((key, route, actor_user_id))
        if not row:
            return None
        created_at: datetime = row["created_at"]
        if created_at < _utcnow() - timedelta(hours=max_age_hours):
            return None
        return deepcopy(row["response_snapshot"])

    def save(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        response_snapshot: dict[str, Any],
    ) -> None:
        self._rows[(key, route, actor_user_id)] = {
            "created_at": _utcnow(),
            "response_snapshot": deepcopy(response_snapshot),
            "id": str(uuid4()),
        }
