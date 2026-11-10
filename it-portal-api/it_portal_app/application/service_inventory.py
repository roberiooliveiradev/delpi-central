"""Casos de uso de serviços/aplicações e da hospedagem deles em servidores."""

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
    SERVICE_SORT_KEYS,
    Actor,
    AuditEvent,
    InventoryRepository,
    ItPortalRepository,
    ServiceQuery,
)
from it_portal_app.domain.catalogs import (
    CRITICALITIES,
    ENVIRONMENTS,
    SERVICE_KINDS,
    UNIT_CODES,
)
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.domain.inventory_links import build_hosting_fields
from it_portal_app.domain.it_services import SERVICE_FIELD_NAMES, build_service_fields
from it_portal_app.domain.servers import diff_fields


def service_archived_error() -> ConflictError:
    return ConflictError(
        "service_archived", "Serviço arquivado: restaure o cadastro antes de alterá-lo."
    )


def server_archived_error() -> ConflictError:
    return ConflictError(
        "server_archived", "Servidor arquivado: restaure o cadastro antes de vinculá-lo."
    )


class ServiceInventory:
    def __init__(self, inventory: InventoryRepository, servers: ItPortalRepository):
        self._repo = inventory
        self._servers = servers

    # ------------------------------------------------------------- services

    def list_services(self, query: ServiceQuery) -> dict:
        normalized = normalize_listing(
            query,
            sort_keys=SERVICE_SORT_KEYS,
            choices={
                "service_kind": SERVICE_KINDS,
                "environment": ENVIRONMENTS,
                "unit_code": UNIT_CODES,
                "criticality": CRITICALITIES,
            },
        )
        items, total = self._repo.list_services(normalized)
        return page_result(items, total, normalized)

    def get_service(self, service_id: str) -> dict:
        service = self._repo.get_service(service_id)
        if service is None:
            raise NotFoundError("service_not_found", "Serviço não encontrado.")
        return service

    def create_service(self, raw: dict, actor: Actor) -> dict:
        fields = build_service_fields(raw)
        service_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="service",
            entity_id=service_id,
            server_id=None,
            event_type="service_created",
            changes={"fields": fields.as_dict()},
            subject_ids=(service_id,),
        )
        return self._repo.insert_service(service_id, fields, actor, audit)

    def update_service(
        self, service_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(service_id)
        fields = build_service_fields(raw)
        changes = diff_fields(current, fields.as_dict(), SERVICE_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise revision_conflict()
            return current
        audit = AuditEvent(
            entity_type="service",
            entity_id=service_id,
            server_id=None,
            event_type="service_updated",
            changes=changes,
            subject_ids=(service_id,),
        )
        updated = self._repo.update_service(service_id, fields, expected_revision, actor, audit)
        if updated is None:
            raise revision_conflict()
        return updated

    def archive_service(self, service_id: str, expected_revision: int, actor: Actor) -> dict:
        self._require_active(service_id)
        return self._set_archived(service_id, True, expected_revision, actor)

    def restore_service(self, service_id: str, expected_revision: int, actor: Actor) -> dict:
        current = self.get_service(service_id)
        if not current["archived"]:
            raise ConflictError("service_not_archived", "O serviço já está ativo.")
        return self._set_archived(service_id, False, expected_revision, actor)

    def list_history(self, service_id: str) -> list[dict]:
        self.get_service(service_id)
        return self._repo.list_subject_history(service_id, HISTORY_LIMIT)

    # ------------------------------------------------------------- hostings

    def list_service_hostings(self, service_id: str) -> list[dict]:
        self.get_service(service_id)
        return self._repo.list_hostings(service_id=service_id)

    def list_server_hostings(self, server_id: str) -> list[dict]:
        if self._servers.get_server(server_id) is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return self._repo.list_hostings(server_id=server_id)

    def link_service_to_server(self, raw: dict, actor: Actor) -> dict:
        fields = build_hosting_fields(raw)
        service = self._repo.get_service(fields.service_id)
        if service is None:
            raise reference_not_found("service_id", "Serviço não encontrado.")
        server = self._servers.get_server(fields.server_id)
        if server is None:
            raise reference_not_found("server_id", "Servidor não encontrado.")
        if service["archived"]:
            raise service_archived_error()
        if server["archived"]:
            raise server_archived_error()
        hosting_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="service_hosting",
            entity_id=hosting_id,
            server_id=server["id"],
            event_type="service_hosting_created",
            changes=_hosting_snapshot(service, server, fields.runtime, fields.instance_name),
            subject_ids=(service["id"], server["id"]),
        )
        return self._repo.insert_hosting(hosting_id, fields, actor, audit)

    def unlink_hosting(self, hosting_id: str, actor: Actor) -> None:
        hosting = self._repo.get_hosting(hosting_id)
        if hosting is None:
            raise NotFoundError("service_hosting_not_found", "Vínculo não encontrado.")
        audit = AuditEvent(
            entity_type="service_hosting",
            entity_id=hosting_id,
            server_id=hosting["server_id"],
            event_type="service_hosting_removed",
            changes=_hosting_snapshot(
                hosting["service"], hosting["server"], hosting["runtime"], hosting["instance_name"]
            ),
            subject_ids=(hosting["service_id"], hosting["server_id"]),
        )
        if not self._repo.delete_hosting(hosting_id, actor, audit):
            raise NotFoundError("service_hosting_not_found", "Vínculo não encontrado.")

    # -------------------------------------------------------------- helpers

    def _require_active(self, service_id: str) -> dict:
        service = self.get_service(service_id)
        if service["archived"]:
            raise service_archived_error()
        return service

    def _set_archived(
        self, service_id: str, archived: bool, expected_revision: int, actor: Actor
    ) -> dict:
        audit = AuditEvent(
            entity_type="service",
            entity_id=service_id,
            server_id=None,
            event_type="service_archived" if archived else "service_restored",
            subject_ids=(service_id,),
        )
        updated = self._repo.set_service_archived(
            service_id, archived, expected_revision, actor, audit
        )
        if updated is None:
            raise revision_conflict()
        return updated


def _hosting_snapshot(service: dict, server: dict, runtime: str, instance_name: str | None) -> dict:
    return {
        "service": {"id": service["id"], "code": service["code"], "name": service["name"]},
        "server": {"id": server["id"], "code": server["code"], "name": server["name"]},
        "runtime": runtime,
        "instance_name": instance_name,
    }
