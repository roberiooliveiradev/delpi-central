"""Casos de uso de integrações e dependências operacionais entre serviços (E2B)."""

from __future__ import annotations

import uuid

from it_portal_app.application.inventory_rules import (
    HISTORY_LIMIT,
    normalize_listing,
    page_result,
    reference_not_found,
    revision_conflict,
)
from it_portal_app.application.ports import (
    INTEGRATION_SORT_KEYS,
    Actor,
    AuditEvent,
    ConnectivityRepository,
    IntegrationQuery,
    InventoryRepository,
    ItPortalRepository,
)
from it_portal_app.application.service_inventory import service_archived_error
from it_portal_app.domain.catalogs import (
    ADMINISTRATIVE_STATUSES,
    CRITICALITIES,
    INTEGRATION_PROTOCOLS,
)
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.domain.integrations import (
    INTEGRATION_FIELD_NAMES,
    IntegrationFields,
    build_integration_fields,
    build_service_dependency_fields,
)
from it_portal_app.domain.servers import diff_fields

RELATED_LIST_LIMIT = 500


def integration_archived_error() -> ConflictError:
    return ConflictError(
        "integration_archived", "Integração arquivada: restaure o cadastro antes de alterá-la."
    )


class IntegrationInventory:
    def __init__(
        self,
        connectivity: ConnectivityRepository,
        inventory: InventoryRepository,
        servers: ItPortalRepository,
    ):
        self._repo = connectivity
        self._inventory = inventory
        self._servers = servers

    # --------------------------------------------------------- integrations

    def list_integrations(self, query: IntegrationQuery) -> dict:
        normalized = normalize_listing(
            query,
            sort_keys=INTEGRATION_SORT_KEYS,
            choices={
                "protocol": INTEGRATION_PROTOCOLS,
                "criticality": CRITICALITIES,
                "administrative_status": ADMINISTRATIVE_STATUSES,
            },
        )
        items, total = self._repo.list_integrations(normalized)
        return page_result(items, total, normalized)

    def get_integration(self, integration_id: str) -> dict:
        integration = self._repo.get_integration(integration_id)
        if integration is None:
            raise NotFoundError("integration_not_found", "Integração não encontrada.")
        return integration

    def create_integration(self, raw: dict, actor: Actor) -> dict:
        fields = build_integration_fields(raw)
        self._require_active_endpoints(fields, fields.internal_service_ids())
        integration_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="integration",
            entity_id=integration_id,
            server_id=None,
            event_type="integration_created",
            changes={"fields": fields.as_dict()},
            subject_ids=(integration_id, *fields.internal_service_ids()),
        )
        return self._repo.insert_integration(integration_id, fields, actor, audit)

    def update_integration(
        self, integration_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(integration_id)
        fields = build_integration_fields(raw)
        changes = diff_fields(current, fields.as_dict(), INTEGRATION_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise revision_conflict()
            return current
        previous = {current["source_service_id"], current["target_service_id"]} - {None}
        added = tuple(sid for sid in fields.internal_service_ids() if sid not in previous)
        self._require_active_endpoints(fields, added)
        subjects = {integration_id, *previous, *fields.internal_service_ids()}
        audit = AuditEvent(
            entity_type="integration",
            entity_id=integration_id,
            server_id=None,
            event_type="integration_updated",
            changes=changes,
            subject_ids=tuple(sorted(subjects)),
        )
        updated = self._repo.update_integration(
            integration_id, fields, expected_revision, actor, audit
        )
        if updated is None:
            raise revision_conflict()
        return updated

    def archive_integration(
        self, integration_id: str, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(integration_id)
        return self._set_archived(current, True, expected_revision, actor)

    def restore_integration(
        self, integration_id: str, expected_revision: int, actor: Actor
    ) -> dict:
        current = self.get_integration(integration_id)
        if not current["archived"]:
            raise ConflictError("integration_not_archived", "A integração já está ativa.")
        return self._set_archived(current, False, expected_revision, actor)

    def list_history(self, integration_id: str) -> list[dict]:
        self.get_integration(integration_id)
        return self._inventory.list_subject_history(integration_id, HISTORY_LIMIT)

    def list_service_integrations(self, service_id: str) -> list[dict]:
        self._require_service(service_id)
        items, _ = self._repo.list_integrations(
            IntegrationQuery(service_id=service_id, archived="all", page_size=RELATED_LIST_LIMIT)
        )
        return items

    def list_server_integrations(self, server_id: str) -> list[dict]:
        if self._servers.get_server(server_id) is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return self._repo.list_server_integrations(server_id)

    # --------------------------------------------------------- dependencies

    def list_service_dependencies(self, service_id: str) -> list[dict]:
        self._require_service(service_id)
        return self._repo.list_dependencies(service_id)

    def link_dependency(self, raw: dict, actor: Actor) -> dict:
        fields = build_service_dependency_fields(raw)
        dependent = self._inventory.get_service(fields.dependent_service_id)
        if dependent is None:
            raise reference_not_found("dependent_service_id", "Serviço não encontrado.")
        required = self._inventory.get_service(fields.required_service_id)
        if required is None:
            raise reference_not_found("required_service_id", "Serviço não encontrado.")
        if dependent["archived"] or required["archived"]:
            raise service_archived_error()
        dependency_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="service_dependency",
            entity_id=dependency_id,
            server_id=None,
            event_type="service_dependency_created",
            changes=_dependency_snapshot(dependent, required),
            subject_ids=(dependent["id"], required["id"]),
        )
        return self._repo.insert_dependency(dependency_id, fields, actor, audit)

    def unlink_dependency(self, dependency_id: str, actor: Actor) -> None:
        dependency = self._repo.get_dependency(dependency_id)
        if dependency is None:
            raise NotFoundError("service_dependency_not_found", "Dependência não encontrada.")
        audit = AuditEvent(
            entity_type="service_dependency",
            entity_id=dependency_id,
            server_id=None,
            event_type="service_dependency_removed",
            changes=_dependency_snapshot(
                dependency["dependent_service"], dependency["required_service"]
            ),
            subject_ids=(dependency["dependent_service_id"], dependency["required_service_id"]),
        )
        if not self._repo.delete_dependency(dependency_id, actor, audit):
            raise NotFoundError("service_dependency_not_found", "Dependência não encontrada.")

    # -------------------------------------------------------------- helpers

    def _require_service(self, service_id: str) -> dict:
        service = self._inventory.get_service(service_id)
        if service is None:
            raise NotFoundError("service_not_found", "Serviço não encontrado.")
        return service

    def _require_active_endpoints(
        self, fields: IntegrationFields, service_ids: tuple[str, ...]
    ) -> None:
        for side in ("source", "target"):
            service_id = getattr(fields, f"{side}_service_id")
            if service_id not in service_ids:
                continue
            service = self._inventory.get_service(service_id)
            if service is None:
                raise reference_not_found(f"{side}_service_id", "Serviço não encontrado.")
            if service["archived"]:
                raise service_archived_error()

    def _require_active(self, integration_id: str) -> dict:
        integration = self.get_integration(integration_id)
        if integration["archived"]:
            raise integration_archived_error()
        return integration

    def _set_archived(
        self, current: dict, archived: bool, expected_revision: int, actor: Actor
    ) -> dict:
        services = tuple(
            sid for sid in (current["source_service_id"], current["target_service_id"]) if sid
        )
        audit = AuditEvent(
            entity_type="integration",
            entity_id=current["id"],
            server_id=None,
            event_type="integration_archived" if archived else "integration_restored",
            subject_ids=(current["id"], *services),
        )
        updated = self._repo.set_integration_archived(
            current["id"], archived, expected_revision, actor, audit
        )
        if updated is None:
            raise revision_conflict()
        return updated


def _dependency_snapshot(dependent: dict, required: dict) -> dict:
    return {
        "dependent_service": {
            "id": dependent["id"],
            "code": dependent["code"],
            "name": dependent["name"],
        },
        "required_service": {
            "id": required["id"],
            "code": required["code"],
            "name": required["name"],
        },
    }
