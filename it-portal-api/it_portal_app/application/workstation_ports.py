"""Contratos G1-API isolados do inventario de servidores e do motor remoto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.domain.workstations import WorkstationFields

WORKSTATION_SORT_KEYS = ("name", "hostname", "device_kind", "updated_at", "created_at")


@dataclass(frozen=True)
class WorkstationQuery:
    q: str | None = None
    unit_code: str | None = None
    device_kind: str | None = None
    administrative_status: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


class WorkstationRepository(Protocol):
    def list_workstations(self, query: WorkstationQuery) -> tuple[list[dict], int]: ...

    def get_workstation(self, workstation_id: str) -> dict | None: ...

    def insert_workstation(
        self, workstation_id: str, fields: WorkstationFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def update_workstation(
        self,
        workstation_id: str,
        fields: WorkstationFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_workstation_archived(
        self,
        workstation_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def list_history(self, workstation_id: str, limit: int) -> list[dict]: ...
