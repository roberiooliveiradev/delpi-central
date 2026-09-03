from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: str
    user_name: str
    has_access: bool = False
    has_create: bool = False
    has_process: bool = False
    has_manage: bool = False
    has_view_all: bool = False
    branch_codes: frozenset[str] = field(default_factory=frozenset)

    @property
    def can_view_all(self) -> bool:
        return self.has_view_all or self.has_process or self.has_manage


@dataclass(slots=True)
class RequestType:
    id: UUID | str
    code: str
    name: str
    permission_prefix: str
    workflow_definition: dict[str, Any]
    presentation_mode: str = "specialized"
    branch_scope: str = "optional"
    active: bool = True
    version: int = 1
    category: str = "general"
    icon: str = "file-text"
    description: str | None = None
    form_schema: dict[str, Any] = field(default_factory=dict)
    ui_schema: dict[str, Any] = field(default_factory=dict)
    destination_config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Request:
    id: UUID | str
    request_number: str
    request_type_id: UUID | str
    type_code: str
    status: str
    created_by_user_id: str
    created_by_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"
    branch_code: str | None = None
    return_reason: str | None = None
    cancel_justification: str | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


@dataclass(slots=True)
class StatusHistoryEntry:
    from_status: str | None
    to_status: str
    action: str
    actor_user_id: str
    actor_name: str
    justification: str | None = None
    changes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AssignmentEntry:
    role: str
    assignee_user_id: str | None = None
    queue_code: str | None = None


@dataclass(slots=True)
class TransitionResult:
    request: Request
    history: StatusHistoryEntry
    assignment: AssignmentEntry | None = None
    domain_events: list[dict[str, Any]] = field(default_factory=list)
