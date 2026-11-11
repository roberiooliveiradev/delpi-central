"""Contratos que a aplicação exige da persistência (implementados em infrastructure)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from it_portal_app.domain.action_plans import ActionPlanFields
from it_portal_app.domain.database_instances import DatabaseInstanceFields
from it_portal_app.domain.integrations import IntegrationFields, ServiceDependencyFields
from it_portal_app.domain.inventory_links import ConsumerFields, HostingFields
from it_portal_app.domain.it_services import ServiceFields
from it_portal_app.domain.networks import NetworkFields, ServerNetworkLinkFields
from it_portal_app.domain.observations import ObservationIngest
from it_portal_app.domain.servers import ServerFields


@dataclass(frozen=True)
class Actor:
    """Pessoa autenticada que executa a operação (identidade resolvida pelo Core)."""

    id: str
    name: str


@dataclass(frozen=True)
class AuditEvent:
    """Evento auditado. `server_id` é o servidor dono do evento (quando houver);
    `subject_ids` lista os demais recursos cujo histórico deve exibi-lo."""

    entity_type: str
    entity_id: str
    server_id: str | None
    event_type: str
    changes: dict = field(default_factory=dict)
    subject_ids: tuple[str, ...] = ()


SERVER_SORT_KEYS = ("name", "hostname", "criticality", "environment", "created_at", "updated_at")
ACTION_SORT_KEYS = ("due_date", "priority", "status", "created_at", "updated_at", "title")
SERVICE_SORT_KEYS = ("name", "criticality", "environment", "created_at", "updated_at")
DATABASE_SORT_KEYS = ("name", "dbms", "criticality", "environment", "created_at", "updated_at")
NETWORK_SORT_KEYS = ("name", "criticality", "environment", "created_at", "updated_at")
INTEGRATION_SORT_KEYS = ("name", "criticality", "protocol", "created_at", "updated_at")


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


@dataclass(frozen=True)
class ServiceQuery:
    q: str | None = None
    service_kind: str | None = None
    environment: str | None = None
    unit_code: str | None = None
    criticality: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


@dataclass(frozen=True)
class DatabaseQuery:
    q: str | None = None
    dbms: str | None = None
    environment: str | None = None
    criticality: str | None = None
    server_id: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


class InventoryRepository(Protocol):
    """Serviços, instâncias de banco e vínculos (E2A).

    Inserções de vínculo/instância validam na mesma transação que o recurso
    referenciado existe e está ativo (levantam NotFound/Conflict de domínio).
    Updates retornam None quando a `revision` diverge ou o registro está
    arquivado.
    """

    def list_services(self, query: ServiceQuery) -> tuple[list[dict], int]: ...

    def get_service(self, service_id: str) -> dict | None: ...

    def insert_service(
        self, service_id: str, fields: ServiceFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def update_service(
        self,
        service_id: str,
        fields: ServiceFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_service_archived(
        self,
        service_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def list_hostings(
        self, *, service_id: str | None = None, server_id: str | None = None
    ) -> list[dict]: ...

    def get_hosting(self, hosting_id: str) -> dict | None: ...

    def insert_hosting(
        self, hosting_id: str, fields: HostingFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def delete_hosting(self, hosting_id: str, actor: Actor, audit: AuditEvent) -> bool: ...

    def list_databases(self, query: DatabaseQuery) -> tuple[list[dict], int]: ...

    def get_database(self, database_id: str) -> dict | None: ...

    def insert_database(
        self,
        database_id: str,
        fields: DatabaseInstanceFields,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict: ...

    def update_database(
        self,
        database_id: str,
        fields: DatabaseInstanceFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_database_archived(
        self,
        database_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def list_consumers(
        self, *, database_id: str | None = None, service_id: str | None = None
    ) -> list[dict]: ...

    def get_consumer(self, consumer_id: str) -> dict | None: ...

    def insert_consumer(
        self, consumer_id: str, fields: ConsumerFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def delete_consumer(self, consumer_id: str, actor: Actor, audit: AuditEvent) -> bool: ...

    def list_subject_history(self, subject_id: str, limit: int) -> list[dict]: ...


@dataclass(frozen=True)
class NetworkQuery:
    q: str | None = None
    unit_code: str | None = None
    environment: str | None = None
    network_scope: str | None = None
    criticality: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


@dataclass(frozen=True)
class IntegrationQuery:
    q: str | None = None
    service_id: str | None = None
    protocol: str | None = None
    criticality: str | None = None
    administrative_status: str | None = None
    archived: str = "active"
    sort: str = "name"
    direction: str = "asc"
    page: int = 1
    page_size: int = 25


class ConnectivityRepository(Protocol):
    """Redes, conectividade servidor↔rede, integrações e dependências (E2B).

    Mesmas garantias do `InventoryRepository`: referência ativa revalidada na
    transação, pares únicos, revisão otimista e auditoria na mesma transação.
    """

    def list_networks(self, query: NetworkQuery) -> tuple[list[dict], int]: ...

    def get_network(self, network_id: str) -> dict | None: ...

    def insert_network(
        self, network_id: str, fields: NetworkFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def update_network(
        self,
        network_id: str,
        fields: NetworkFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_network_archived(
        self,
        network_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def list_network_links(
        self, *, network_id: str | None = None, server_id: str | None = None
    ) -> list[dict]: ...

    def get_network_link(self, link_id: str) -> dict | None: ...

    def insert_network_link(
        self, link_id: str, fields: ServerNetworkLinkFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def delete_network_link(self, link_id: str, actor: Actor, audit: AuditEvent) -> bool: ...

    def list_integrations(self, query: IntegrationQuery) -> tuple[list[dict], int]: ...

    def get_integration(self, integration_id: str) -> dict | None: ...

    def list_server_integrations(self, server_id: str) -> list[dict]: ...

    def insert_integration(
        self, integration_id: str, fields: IntegrationFields, actor: Actor, audit: AuditEvent
    ) -> dict: ...

    def update_integration(
        self,
        integration_id: str,
        fields: IntegrationFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def set_integration_archived(
        self,
        integration_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None: ...

    def list_dependencies(self, service_id: str) -> list[dict]: ...

    def get_dependency(self, dependency_id: str) -> dict | None: ...

    def insert_dependency(
        self,
        dependency_id: str,
        fields: ServiceDependencyFields,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict: ...

    def delete_dependency(self, dependency_id: str, actor: Actor, audit: AuditEvent) -> bool: ...


class ObservationRepository(Protocol):
    """Observações automáticas de servidores (E4.S1).

    Idempotência por `run_id`. Nunca cria nem altera o cadastro manual do servidor.
    """

    def get_by_run_id(self, run_id: str) -> dict | None: ...

    def get_latest_for_server(self, server_id: str) -> dict | None: ...

    def list_for_server(self, server_id: str, *, limit: int) -> list[dict]: ...

    def insert_observation(
        self,
        observation_id: str,
        server_id: str,
        ingest: ObservationIngest,
        *,
        collector_client_id: str,
        divergences: list[dict],
        retention: int,
    ) -> dict: ...
