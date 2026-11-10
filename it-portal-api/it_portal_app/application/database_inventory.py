"""Casos de uso das instâncias de banco de dados e dos serviços que as consomem."""

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
    DATABASE_SORT_KEYS,
    Actor,
    AuditEvent,
    DatabaseQuery,
    InventoryRepository,
    ItPortalRepository,
)
from it_portal_app.application.service_inventory import (
    server_archived_error,
    service_archived_error,
)
from it_portal_app.domain.catalogs import CRITICALITIES, DBMS_ENGINES, ENVIRONMENTS
from it_portal_app.domain.database_instances import (
    DATABASE_FIELD_NAMES,
    build_database_fields,
)
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.domain.inventory_links import build_consumer_fields
from it_portal_app.domain.servers import diff_fields


def database_archived_error() -> ConflictError:
    return ConflictError(
        "database_instance_archived",
        "Instância arquivada: restaure o cadastro antes de alterá-la.",
    )


class DatabaseInventory:
    def __init__(self, inventory: InventoryRepository, servers: ItPortalRepository):
        self._repo = inventory
        self._servers = servers

    # ------------------------------------------------------------ instances

    def list_databases(self, query: DatabaseQuery) -> dict:
        normalized = normalize_listing(
            query,
            sort_keys=DATABASE_SORT_KEYS,
            choices={
                "dbms": DBMS_ENGINES,
                "environment": ENVIRONMENTS,
                "criticality": CRITICALITIES,
            },
        )
        items, total = self._repo.list_databases(normalized)
        return page_result(items, total, normalized)

    def get_database(self, database_id: str) -> dict:
        database = self._repo.get_database(database_id)
        if database is None:
            raise NotFoundError("database_instance_not_found", "Instância de banco não encontrada.")
        return database

    def create_database(self, raw: dict, actor: Actor) -> dict:
        fields = build_database_fields(raw)
        self._require_active_host(fields.server_id)
        database_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="database_instance",
            entity_id=database_id,
            server_id=fields.server_id,
            event_type="database_instance_created",
            changes={"fields": fields.as_dict()},
            subject_ids=(database_id, fields.server_id),
        )
        return self._repo.insert_database(database_id, fields, actor, audit)

    def update_database(
        self, database_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(database_id)
        fields = build_database_fields(raw)
        changes = diff_fields(current, fields.as_dict(), DATABASE_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise revision_conflict()
            return current
        if "server_id" in changes:
            self._require_active_host(fields.server_id)
        subjects = {database_id, current["server_id"], fields.server_id}
        audit = AuditEvent(
            entity_type="database_instance",
            entity_id=database_id,
            server_id=fields.server_id,
            event_type="database_instance_updated",
            changes=changes,
            subject_ids=tuple(sorted(subjects)),
        )
        updated = self._repo.update_database(database_id, fields, expected_revision, actor, audit)
        if updated is None:
            raise revision_conflict()
        return updated

    def archive_database(self, database_id: str, expected_revision: int, actor: Actor) -> dict:
        current = self._require_active(database_id)
        return self._set_archived(current, True, expected_revision, actor)

    def restore_database(self, database_id: str, expected_revision: int, actor: Actor) -> dict:
        current = self.get_database(database_id)
        if not current["archived"]:
            raise ConflictError("database_instance_not_archived", "A instância já está ativa.")
        return self._set_archived(current, False, expected_revision, actor)

    def list_history(self, database_id: str) -> list[dict]:
        self.get_database(database_id)
        return self._repo.list_subject_history(database_id, HISTORY_LIMIT)

    # ------------------------------------------------------------ consumers

    def list_database_consumers(self, database_id: str) -> list[dict]:
        self.get_database(database_id)
        return self._repo.list_consumers(database_id=database_id)

    def list_service_databases(self, service_id: str) -> list[dict]:
        if self._repo.get_service(service_id) is None:
            raise NotFoundError("service_not_found", "Serviço não encontrado.")
        return self._repo.list_consumers(service_id=service_id)

    def link_consumer(self, raw: dict, actor: Actor) -> dict:
        fields = build_consumer_fields(raw)
        database = self._repo.get_database(fields.database_instance_id)
        if database is None:
            raise reference_not_found("database_instance_id", "Instância de banco não encontrada.")
        service = self._repo.get_service(fields.service_id)
        if service is None:
            raise reference_not_found("service_id", "Serviço não encontrado.")
        if database["archived"]:
            raise database_archived_error()
        if service["archived"]:
            raise service_archived_error()
        consumer_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="database_consumer",
            entity_id=consumer_id,
            server_id=None,
            event_type="database_consumer_created",
            changes=_consumer_snapshot(database, service),
            subject_ids=(database["id"], service["id"]),
        )
        return self._repo.insert_consumer(consumer_id, fields, actor, audit)

    def unlink_consumer(self, consumer_id: str, actor: Actor) -> None:
        consumer = self._repo.get_consumer(consumer_id)
        if consumer is None:
            raise NotFoundError("database_consumer_not_found", "Vínculo não encontrado.")
        audit = AuditEvent(
            entity_type="database_consumer",
            entity_id=consumer_id,
            server_id=None,
            event_type="database_consumer_removed",
            changes=_consumer_snapshot(consumer["database"], consumer["service"]),
            subject_ids=(consumer["database_instance_id"], consumer["service_id"]),
        )
        if not self._repo.delete_consumer(consumer_id, actor, audit):
            raise NotFoundError("database_consumer_not_found", "Vínculo não encontrado.")

    # -------------------------------------------------------------- helpers

    def _require_active(self, database_id: str) -> dict:
        database = self.get_database(database_id)
        if database["archived"]:
            raise database_archived_error()
        return database

    def _require_active_host(self, server_id: str) -> None:
        server = self._servers.get_server(server_id)
        if server is None:
            raise reference_not_found("server_id", "Servidor não encontrado.")
        if server["archived"]:
            raise server_archived_error()

    def _set_archived(
        self, current: dict, archived: bool, expected_revision: int, actor: Actor
    ) -> dict:
        audit = AuditEvent(
            entity_type="database_instance",
            entity_id=current["id"],
            server_id=current["server_id"],
            event_type="database_instance_archived" if archived else "database_instance_restored",
            subject_ids=(current["id"], current["server_id"]),
        )
        updated = self._repo.set_database_archived(
            current["id"], archived, expected_revision, actor, audit
        )
        if updated is None:
            raise revision_conflict()
        return updated


def _consumer_snapshot(database: dict, service: dict) -> dict:
    return {
        "database_instance": {
            "id": database["id"],
            "code": database["code"],
            "name": database["name"],
        },
        "service": {"id": service["id"], "code": service["code"], "name": service["name"]},
    }
