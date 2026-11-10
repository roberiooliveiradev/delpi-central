"""Contratos que a aplicação exige da persistência (implementados em infrastructure)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from it_portal_app.domain.action_plans import ActionPlanFields
from it_portal_app.domain.servers import ServerFields


@dataclass(frozen=True)
class Actor:
    """Pessoa autenticada que executa a operação (identidade resolvida pelo Core)."""

    id: str
    name: str


@dataclass(frozen=True)
class AuditEvent:
    entity_type: str
    entity_id: str
    server_id: str
    event_type: str
    changes: dict = field(default_factory=dict)


SERVER_SORT_KEYS = ("name", "hostname", "criticality", "environment", "created_at", "updated_at")
ACTION_SORT_KEYS = ("due_date", "priority", "status", "created_at", "updated_at", "title")


@dataclass(frozen=True)
class ServerQuery:
    q: str | None = None
    unit_code: str | None = None
    environment: str | None = None
    criticality: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


@dataclass(frozen=True)
class ActionPlanQuery:
    today: date
    statuses: tuple[str, ...] = ()
    server_id: str | None = None
    priority: str | None = None
    overdue_only: bool = False
    q: str | None = None
    sort: str = "due_date"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


class ItPortalRepository(Protocol):
    def list_servers(self, query: ServerQuery) -> tuple[list[dict], int]: ...

    def get_server(self, server_id: str) -> dict | None: ...

    def insert_server(
        self, server_id: str, fields: ServerFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def update_server(
        self,
        server_id: str,
        fields: ServerFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_server_archived(
        self,
        server_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def count_open_action_plans(self, server_id: str) -> int: ...

    def list_notes(self, server_id: str) -> list[dict]: ...

    def insert_note(
        self, note_id: str, server_id: str, body: str, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def list_server_history(self, server_id: str, limit: int) -> list[dict]: ...

    def list_action_plans(self, query: ActionPlanQuery) -> tuple[list[dict], int]: ...

    def get_action_plan(self, action_plan_id: str) -> dict | None: ...

    def insert_action_plan(
        self,
        action_plan_id: str,
        server_id: str,
        fields: ActionPlanFields,
        status: str,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict: ...

    def update_action_plan(
        self,
        action_plan_id: str,
        fields: ActionPlanFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def update_action_plan_status(
        self,
        action_plan_id: str,
        status: str,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def dashboard_counts(self, today: date) -> dict: ...

    def recent_servers(self, limit: int) -> list[dict]: ...

    def attention_action_plans(self, today: date, limit: int) -> list[dict]: ...
