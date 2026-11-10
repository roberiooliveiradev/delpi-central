"""Contrato HTTP do Portal de TI (documentado no OpenAPI).

Entradas aceitam strings livres com limites de tamanho de transporte; a
validação de negócio (hostname, IP, catálogos, segredos) fica no domínio e
responde 422 com erros por campo.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

_TRANSPORT_MAX = 5000


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServerInput(_Input):
    name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    hostname: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    ip_address: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    unit_code: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    location: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    environment: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    server_type: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    purpose: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    operating_system: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    criticality: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    administrative_status: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    description: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class ServerUpdateInput(ServerInput):
    revision: int = Field(ge=1)


class RevisionInput(_Input):
    revision: int = Field(ge=1)


class NoteInput(_Input):
    body: str = Field(max_length=_TRANSPORT_MAX)


class ActionPlanInput(_Input):
    title: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    description: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    priority: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    due_date: str | None = Field(default=None, max_length=32)


class ActionPlanUpdateInput(ActionPlanInput):
    revision: int = Field(ge=1)


class ActionPlanStatusInput(_Input):
    status: str = Field(max_length=32)
    revision: int = Field(ge=1)


class ServerOut(BaseModel):
    id: str
    code: str
    name: str
    hostname: str
    ip_address: str | None
    unit_code: str
    location: str | None
    environment: str
    server_type: str
    purpose: str | None
    operating_system: str | None
    criticality: str
    administrative_status: str
    responsible: str | None
    description: str | None
    revision: int
    archived: bool
    archived_at: datetime | None
    archived_by_name: str | None
    open_action_count: int
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class NoteOut(BaseModel):
    id: str
    server_id: str
    body: str
    author_name: str
    created_at: datetime


class HistoryEventOut(BaseModel):
    id: str
    entity_type: Literal["server", "server_note", "action_plan"]
    entity_id: str
    event_type: str
    changes: dict
    actor_name: str
    occurred_at: datetime


class ServerSummaryOut(BaseModel):
    id: str
    code: str
    name: str
    hostname: str
    environment: str
    unit_code: str
    archived: bool


class ActionPlanOut(BaseModel):
    id: str
    code: str
    server_id: str
    server: ServerSummaryOut
    title: str
    description: str | None
    responsible: str | None
    priority: str
    status: str
    due_date: date | None
    completed_at: datetime | None
    is_overdue: bool
    revision: int
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class PageOut(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ServerCountsOut(BaseModel):
    total: int
    high_or_critical: int


class ActionCountsOut(BaseModel):
    open: int
    overdue: int


class DashboardOut(BaseModel):
    reference_date: date
    generated_at: datetime
    servers: ServerCountsOut
    recent_servers: list[ServerOut]
    action_plans: ActionCountsOut | None = Field(
        description="Ausente (null) sem a permissão it-portal.actions.view."
    )
    attention_action_plans: list[ActionPlanOut] | None


class CapabilitiesOut(BaseModel):
    display_name: str
    can_view_servers: bool
    can_manage_servers: bool
    can_create_notes: bool
    can_view_action_plans: bool
    can_manage_action_plans: bool


class HealthOut(BaseModel):
    status: str
    service: str


class ResponseMeta(BaseModel):
    operationId: str


class Envelope(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T
    meta: ResponseMeta | None = None


class ErrorDetail(BaseModel):
    code: str
    details: dict | None = None


class ErrorData(BaseModel):
    error: ErrorDetail


class ErrorEnvelope(BaseModel):
    success: Literal[False]
    message: str
    data: ErrorData | None = None
    meta: ResponseMeta | None = None


ERROR_RESPONSES: dict[int | str, dict] = {
    401: {"description": "Não autenticado."},
    403: {"description": "Sem permissão efetiva no Core."},
    404: {"model": ErrorEnvelope, "description": "Recurso não encontrado."},
    409: {"model": ErrorEnvelope, "description": "Conflito de estado ou revisão."},
    422: {"model": ErrorEnvelope, "description": "Dados inválidos."},
    503: {"description": "Autorização ou armazenamento indisponível."},
}
