"""Contrato HTTP do Portal de TI (documentado no OpenAPI).

Entradas aceitam strings livres com limites de tamanho de transporte; a
validação de negócio (hostname, IP, catálogos, segredos) fica no domínio e
responde 422 com erros por campo.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
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


HistoryEntityType = Literal[
    "server",
    "server_note",
    "action_plan",
    "service",
    "service_hosting",
    "database_instance",
    "database_consumer",
    "network",
    "server_network_link",
    "integration",
    "service_dependency",
    "host_service_preference",
]


class HistoryEventOut(BaseModel):
    id: str
    entity_type: HistoryEntityType
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
    can_manage_host_services: bool
    can_control_host_services: bool
    can_create_notes: bool
    can_view_action_plans: bool
    can_manage_action_plans: bool
    can_view_services: bool
    can_manage_services: bool
    can_view_databases: bool
    can_manage_databases: bool
    can_view_networks: bool
    can_manage_networks: bool
    can_view_integrations: bool
    can_manage_integrations: bool


# ------------------------------------------------------------- inventário E2A

_PortInput = int | str | None


class ServiceInput(_Input):
    name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    description: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    service_kind: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    service_type: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    technology: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    environment: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    unit_code: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    port: _PortInput = Field(default=None, description="1–65535; vazio quando não se aplica.")
    criticality: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    administrative_status: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class ServiceUpdateInput(ServiceInput):
    revision: int = Field(ge=1)


class DatabaseInstanceInput(_Input):
    name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    dbms: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    version: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    server_id: str | None = Field(default=None, max_length=64)
    port: _PortInput = Field(default=None, description="1–65535; vazio quando não se aplica.")
    environment: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    purpose: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    criticality: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    administrative_status: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    technical_notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class DatabaseInstanceUpdateInput(DatabaseInstanceInput):
    revision: int = Field(ge=1)


class ServiceHostingInput(_Input):
    service_id: str | None = Field(default=None, max_length=64)
    server_id: str | None = Field(default=None, max_length=64)
    runtime: str | None = Field(default=None, max_length=64)
    instance_name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class DatabaseConsumerInput(_Input):
    database_instance_id: str | None = Field(default=None, max_length=64)
    service_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class ServiceSummaryOut(BaseModel):
    id: str
    code: str
    name: str
    service_kind: str
    environment: str
    criticality: str
    archived: bool


class DatabaseSummaryOut(BaseModel):
    id: str
    code: str
    name: str
    dbms: str
    environment: str
    criticality: str
    archived: bool


class ServiceOut(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    service_kind: str
    service_type: str
    technology: str | None
    environment: str
    unit_code: str
    port: int | None
    criticality: str
    responsible: str
    administrative_status: str
    revision: int
    archived: bool
    archived_at: datetime | None
    archived_by_name: str | None
    hosting_count: int
    database_count: int
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class DatabaseInstanceOut(BaseModel):
    id: str
    code: str
    name: str
    dbms: str
    version: str | None
    server_id: str
    server: ServerSummaryOut
    port: int | None
    environment: str
    purpose: str | None
    criticality: str
    responsible: str
    administrative_status: str
    technical_notes: str | None
    revision: int
    archived: bool
    archived_at: datetime | None
    archived_by_name: str | None
    consumer_count: int
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class ServiceHostingOut(BaseModel):
    id: str
    service_id: str
    server_id: str
    runtime: str
    instance_name: str | None
    notes: str | None
    created_at: datetime
    created_by_name: str
    service: ServiceSummaryOut
    server: ServerSummaryOut


class LinkRemovedOut(BaseModel):
    id: str = Field(description="Id do vínculo removido. Os recursos ligados são preservados.")


class DatabaseConsumerOut(BaseModel):
    id: str
    database_instance_id: str
    service_id: str
    notes: str | None
    created_at: datetime
    created_by_name: str
    database: DatabaseSummaryOut
    service: ServiceSummaryOut


# ------------------------------------------------------------- inventário E2B


class NetworkInput(_Input):
    name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    cidr: str | None = Field(
        default=None, max_length=64, description="Endereço de rede com prefixo (ex.: 10.0.1.0/24)."
    )
    vlan_id: int | str | None = Field(default=None, description="1–4094; vazio sem VLAN.")
    gateway: str | None = Field(default=None, max_length=64)
    unit_code: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    location: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    purpose: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    environment: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    zone: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    network_scope: str | None = Field(
        default=None,
        max_length=64,
        description="corporate | container_runtime (rede interna de containers).",
    )
    criticality: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class NetworkUpdateInput(NetworkInput):
    revision: int = Field(ge=1)


class ServerNetworkLinkInput(_Input):
    server_id: str | None = Field(default=None, max_length=64)
    network_id: str | None = Field(default=None, max_length=64)
    ip_address: str | None = Field(
        default=None, max_length=64, description="IP do servidor nesta rede (dentro do CIDR)."
    )
    interface_name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class IntegrationInput(_Input):
    name: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    source_service_id: str | None = Field(default=None, max_length=64)
    source_external_name: str | None = Field(
        default=None,
        max_length=_TRANSPORT_MAX,
        description="Sistema externo não cadastrado (exclusivo com source_service_id).",
    )
    target_service_id: str | None = Field(default=None, max_length=64)
    target_external_name: str | None = Field(
        default=None,
        max_length=_TRANSPORT_MAX,
        description="Sistema externo não cadastrado (exclusivo com target_service_id).",
    )
    protocol: str | None = Field(default=None, max_length=64)
    direction: str | None = Field(default=None, max_length=64)
    purpose: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    criticality: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    responsible: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    administrative_status: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class IntegrationUpdateInput(IntegrationInput):
    revision: int = Field(ge=1)


class ServiceDependencyInput(_Input):
    dependent_service_id: str | None = Field(default=None, max_length=64)
    required_service_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class NetworkSummaryOut(BaseModel):
    id: str
    code: str
    name: str
    cidr: str
    vlan_id: int | None
    network_scope: str
    environment: str
    unit_code: str
    archived: bool


class NetworkOut(BaseModel):
    id: str
    code: str
    name: str
    cidr: str
    vlan_id: int | None
    gateway: str | None
    unit_code: str
    location: str | None
    purpose: str | None
    environment: str
    zone: str | None
    network_scope: str
    criticality: str
    responsible: str
    notes: str | None
    revision: int
    archived: bool
    archived_at: datetime | None
    archived_by_name: str | None
    server_count: int
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class ServerNetworkLinkOut(BaseModel):
    id: str
    server_id: str
    network_id: str
    ip_address: str | None
    interface_name: str | None
    notes: str | None
    created_at: datetime
    created_by_name: str
    server: ServerSummaryOut
    network: NetworkSummaryOut


class IntegrationOut(BaseModel):
    id: str
    code: str
    name: str
    source_service_id: str | None
    source_external_name: str | None = Field(
        description="Preenchido quando a origem é um sistema externo não cadastrado."
    )
    source_service: ServiceSummaryOut | None
    target_service_id: str | None
    target_external_name: str | None = Field(
        description="Preenchido quando o destino é um sistema externo não cadastrado."
    )
    target_service: ServiceSummaryOut | None
    protocol: str
    direction: str
    purpose: str | None
    criticality: str
    responsible: str
    administrative_status: str
    notes: str | None
    revision: int
    archived: bool
    archived_at: datetime | None
    archived_by_name: str | None
    created_at: datetime
    created_by_name: str
    updated_at: datetime
    updated_by_name: str


class ServiceDependencyOut(BaseModel):
    id: str
    dependent_service_id: str
    required_service_id: str
    notes: str | None
    created_at: datetime
    created_by_name: str
    dependent_service: ServiceSummaryOut
    required_service: ServiceSummaryOut


class HostIdentityInput(_Input):
    hostname: str | None = Field(default=None, max_length=_TRANSPORT_MAX)
    machine_id: str | None = Field(default=None, max_length=_TRANSPORT_MAX)


class ObservationIngestInput(_Input):
    run_id: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=40)
    schema_version: str | None = Field(default=None, max_length=16)
    status: str | None = Field(default=None, max_length=20)
    observed_at: str | None = Field(default=None, max_length=64)
    host_identity: HostIdentityInput | None = None
    summary: dict | None = None
    sections_status: dict[str, str] | None = None


class ObservationOut(BaseModel):
    id: str
    server_id: str
    run_id: str
    source: str
    collector_client_id: str
    observed_at: datetime
    received_at: datetime
    schema_version: str
    status: str
    summary: dict
    sections_status: dict
    divergences: list
    created_at: datetime
    presentation_status: str | None = None


class HostServiceInput(_Input):
    name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=500)
    state: str
    start_mode: str
    can_stop: bool

class HostServiceBatchInput(_Input):
    run_id: str = Field(max_length=64)
    schema_version: str
    observed_at: str = Field(max_length=64)
    host_identity: HostIdentityInput
    batch_index: int
    batch_count: int
    services: list[HostServiceInput] = Field(min_length=1, max_length=100)

class HostServiceBatchReceipt(BaseModel):
    run_id: str
    server_id: str
    batch_index: int
    received_batches: int
    batch_count: int
    status: str
    applied: bool
    service_count: int

class HostServicePreferenceInput(_Input):
    is_favorite: bool
    criticality: Literal["normal", "high", "critical"]


class HostServicePreferenceOut(BaseModel):
    service_key: str
    is_favorite: bool
    criticality: Literal["normal", "high", "critical"]


class HostServiceOut(BaseModel):
    control_allowed: bool
    service_key: str
    is_favorite: bool
    criticality: Literal["normal", "high", "critical"]
    name: str
    display_name: str
    description: str | None
    state: str
    start_mode: str
    can_stop: bool
    is_present: bool
    observed_at: datetime
    updated_at: datetime

class HostServiceCurrentOut(BaseModel):
    run_id: str
    observed_at: datetime
    received_at: datetime
    service_count: int

class HostServicePage(BaseModel):
    favorites_count: int
    items: list[HostServiceOut]
    total: int
    page: int
    page_size: int
    current: HostServiceCurrentOut | None

class HostServiceActionInput(_Input):
    action: Literal["start", "stop", "restart"]
    request_id: UUID
    confirmed: bool


class HostServiceActionOut(BaseModel):
    id: str
    server_id: str
    service_key: str
    service_name: str
    action: Literal["start", "stop", "restart"]
    state_before: str
    status: Literal["queued", "running", "succeeded", "failed", "timeout"]
    state_after: str | None
    error_code: str | None
    requested_at: datetime
    claimed_at: datetime | None
    finished_at: datetime | None
    requested_by_name: str


class HostServiceAgentClaimOut(BaseModel):
    id: str
    service_key: str
    service_name: str
    action: Literal["start", "stop", "restart"]
    state_before: str
    lease: str


class HostServiceAgentReportInput(_Input):
    lease: str = Field(min_length=24, max_length=128)
    status: Literal["succeeded", "failed"]
    state_after: Literal["running", "stopped", "paused", "unknown"] | None
    error_code: Literal["access_denied", "service_not_found", "not_allowed",
                        "precondition_failed", "dependent_services", "timeout",
                        "execution_failed", "disabled"] | None = None


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
