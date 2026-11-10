"""Repositório de inventário em memória — exclusivo de testes de serviço/HTTP.

Compartilha servidores e trilha de auditoria com `InMemoryItPortalRepository`
e reproduz as garantias observáveis do adapter Postgres: unicidade ativa,
pares únicos de vínculo, referência ativa exigida e revisão otimista. A
paridade real é coberta por `test_postgres_inventory.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from it_portal_app.application.inventory_rules import reference_not_found
from it_portal_app.application.ports import Actor, AuditEvent, DatabaseQuery, ServiceQuery
from it_portal_app.domain.catalogs import CRITICALITY_RANK
from it_portal_app.domain.database_instances import DatabaseInstanceFields, format_database_code
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.inventory_links import ConsumerFields, HostingFields
from it_portal_app.domain.it_services import ServiceFields, format_service_code

from tests.fakes import InMemoryItPortalRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _server_summary(server: dict) -> dict:
    return {
        key: server[key]
        for key in ("id", "code", "name", "hostname", "environment", "unit_code", "archived")
    }


@dataclass
class InMemoryInventoryRepository:
    servers_repo: InMemoryItPortalRepository
    services: dict[str, dict] = field(default_factory=dict)
    hostings: dict[str, dict] = field(default_factory=dict)
    databases: dict[str, dict] = field(default_factory=dict)
    consumers: dict[str, dict] = field(default_factory=dict)
    _service_seq: int = 0
    _database_seq: int = 0

    # ------------------------------------------------------------- helpers

    def _record(self, audit: AuditEvent, actor: Actor) -> None:
        self.servers_repo._record(audit, actor)

    def _active_or_raise(self, store: dict, row_id: str, field_name: str, label: str, code: str):
        row = store.get(row_id)
        if row is None:
            raise reference_not_found(field_name, f"{label} não encontrado.")
        if row["archived"]:
            raise ConflictError(code, f"{label} arquivado.")

    def _service_view(self, service: dict) -> dict:
        return {
            **service,
            "hosting_count": sum(1 for h in self.hostings.values() if h["service_id"] == service["id"]),
            "database_count": sum(
                1 for c in self.consumers.values() if c["service_id"] == service["id"]
            ),
        }

    def _service_summary(self, service_id: str) -> dict:
        service = self.services[service_id]
        return {
            key: service[key]
            for key in ("id", "code", "name", "service_kind", "environment", "criticality", "archived")
        }

    def _database_view(self, database: dict) -> dict:
        server = self.servers_repo.servers[database["server_id"]]
        return {
            **database,
            "server": _server_summary(server),
            "consumer_count": sum(
                1 for c in self.consumers.values() if c["database_instance_id"] == database["id"]
            ),
        }

    def _hosting_view(self, hosting: dict) -> dict:
        return {
            **hosting,
            "service": self._service_summary(hosting["service_id"]),
            "server": _server_summary(self.servers_repo.servers[hosting["server_id"]]),
        }

    def _consumer_view(self, consumer: dict) -> dict:
        database = self.databases[consumer["database_instance_id"]]
        return {
            **consumer,
            "database": {
                key: database[key]
                for key in ("id", "code", "name", "dbms", "environment", "criticality", "archived")
            },
            "service": self._service_summary(consumer["service_id"]),
        }

    @staticmethod
    def _page(items: list[dict], query) -> tuple[list[dict], int]:
        def key(row: dict):
            if query.sort == "criticality":
                primary = CRITICALITY_RANK[row["criticality"]]
            elif query.sort == "name":
                primary = row["name"].lower()
            else:
                primary = row[query.sort]
            return (primary, row["seq"])

        items.sort(key=key, reverse=query.direction == "desc")
        start = (query.page - 1) * query.page_size
        return items[start : start + query.page_size], len(items)

    @staticmethod
    def _archived_filter(items: list[dict], archived: str) -> list[dict]:
        if archived == "active":
            return [row for row in items if not row["archived"]]
        if archived == "archived":
            return [row for row in items if row["archived"]]
        return items

    def _set_archived(self, row: dict, archived: bool, expected_revision: int, actor: Actor):
        if row["revision"] != expected_revision or row["archived"] == archived:
            return False
        row.update(
            archived=archived,
            archived_at=_now() if archived else None,
            archived_by_name=actor.name if archived else None,
            revision=row["revision"] + 1,
            updated_at=_now(),
            updated_by_name=actor.name,
        )
        return True

    # ------------------------------------------------------------ services

    def _ensure_unique_service(self, service_id: str, values: dict) -> None:
        for other in self.services.values():
            if other["id"] == service_id or other["archived"]:
                continue
            if (
                other["unit_code"] == values["unit_code"]
                and other["environment"] == values["environment"]
                and other["name"].lower() == values["name"].lower()
            ):
                raise ConflictError("service_identity_conflict", "duplicado")

    def list_services(self, query: ServiceQuery):
        items = self._archived_filter(list(self.services.values()), query.archived)
        if query.q:
            needle = query.q.lower()
            items = [
                s for s in items if needle in s["name"].lower() or needle in (s["technology"] or "").lower()
            ]
        for column in ("service_kind", "environment", "unit_code", "criticality"):
            value = getattr(query, column)
            if value:
                items = [s for s in items if s[column] == value]
        page, total = self._page(items, query)
        return [self._service_view(s) for s in page], total

    def get_service(self, service_id: str):
        service = self.services.get(service_id)
        return self._service_view(service) if service else None

    def insert_service(self, service_id: str, fields: ServiceFields, actor: Actor, audit: AuditEvent):
        values = fields.as_dict()
        self._ensure_unique_service(service_id, values)
        self._service_seq += 1
        now = _now()
        self.services[service_id] = {
            **values,
            "id": service_id,
            "seq": self._service_seq,
            "code": format_service_code(self._service_seq),
            "revision": 1,
            "archived": False,
            "archived_at": None,
            "archived_by_name": None,
            "created_at": now,
            "created_by_name": actor.name,
            "updated_at": now,
            "updated_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_service(service_id)

    def update_service(self, service_id, fields, expected_revision, actor, audit):
        service = self.services[service_id]
        if service["revision"] != expected_revision or service["archived"]:
            return None
        values = fields.as_dict()
        self._ensure_unique_service(service_id, values)
        service.update(values)
        service.update(revision=service["revision"] + 1, updated_at=_now(), updated_by_name=actor.name)
        self._record(audit, actor)
        return self.get_service(service_id)

    def set_service_archived(self, service_id, archived, expected_revision, actor, audit):
        service = self.services[service_id]
        if not archived and service["archived"]:
            self._ensure_unique_service(service_id, service)
        if not self._set_archived(service, archived, expected_revision, actor):
            return None
        self._record(audit, actor)
        return self.get_service(service_id)

    # ------------------------------------------------------------ hostings

    def list_hostings(self, *, service_id=None, server_id=None):
        rows = [
            h
            for h in self.hostings.values()
            if (service_id is None or h["service_id"] == service_id)
            and (server_id is None or h["server_id"] == server_id)
        ]
        return [self._hosting_view(h) for h in rows]

    def get_hosting(self, hosting_id):
        hosting = self.hostings.get(hosting_id)
        return self._hosting_view(hosting) if hosting else None

    def insert_hosting(self, hosting_id, fields: HostingFields, actor, audit):
        self._active_or_raise(self.services, fields.service_id, "service_id", "Serviço", "service_archived")
        self._active_or_raise(
            self.servers_repo.servers, fields.server_id, "server_id", "Servidor", "server_archived"
        )
        for other in self.hostings.values():
            if other["service_id"] == fields.service_id and other["server_id"] == fields.server_id:
                raise ConflictError("service_hosting_exists", "duplicado")
        self.hostings[hosting_id] = {
            "id": hosting_id,
            "service_id": fields.service_id,
            "server_id": fields.server_id,
            "runtime": fields.runtime,
            "instance_name": fields.instance_name,
            "notes": fields.notes,
            "created_at": _now(),
            "created_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_hosting(hosting_id)

    def delete_hosting(self, hosting_id, actor, audit):
        if self.hostings.pop(hosting_id, None) is None:
            return False
        self._record(audit, actor)
        return True

    # ----------------------------------------------------------- databases

    def _ensure_unique_database(self, database_id: str, values: dict) -> None:
        for other in self.databases.values():
            if other["id"] == database_id or other["archived"]:
                continue
            if other["server_id"] == values["server_id"] and other["name"].lower() == values["name"].lower():
                raise ConflictError("database_identity_conflict", "duplicado")

    def list_databases(self, query: DatabaseQuery):
        items = self._archived_filter(list(self.databases.values()), query.archived)
        if query.q:
            needle = query.q.lower()
            items = [d for d in items if needle in d["name"].lower()]
        for column in ("dbms", "environment", "criticality", "server_id"):
            value = getattr(query, column)
            if value:
                items = [d for d in items if d[column] == value]
        page, total = self._page(items, query)
        return [self._database_view(d) for d in page], total

    def get_database(self, database_id):
        database = self.databases.get(database_id)
        return self._database_view(database) if database else None

    def insert_database(self, database_id, fields: DatabaseInstanceFields, actor, audit):
        self._active_or_raise(
            self.servers_repo.servers, fields.server_id, "server_id", "Servidor", "server_archived"
        )
        values = fields.as_dict()
        self._ensure_unique_database(database_id, values)
        self._database_seq += 1
        now = _now()
        self.databases[database_id] = {
            **values,
            "id": database_id,
            "seq": self._database_seq,
            "code": format_database_code(self._database_seq),
            "revision": 1,
            "archived": False,
            "archived_at": None,
            "archived_by_name": None,
            "created_at": now,
            "created_by_name": actor.name,
            "updated_at": now,
            "updated_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_database(database_id)

    def update_database(self, database_id, fields, expected_revision, actor, audit):
        database = self.databases[database_id]
        if database["revision"] != expected_revision or database["archived"]:
            return None
        if fields.server_id != database["server_id"]:
            self._active_or_raise(
                self.servers_repo.servers, fields.server_id, "server_id", "Servidor", "server_archived"
            )
        values = fields.as_dict()
        self._ensure_unique_database(database_id, values)
        database.update(values)
        database.update(revision=database["revision"] + 1, updated_at=_now(), updated_by_name=actor.name)
        self._record(audit, actor)
        return self.get_database(database_id)

    def set_database_archived(self, database_id, archived, expected_revision, actor, audit):
        database = self.databases[database_id]
        if not archived and database["archived"]:
            self._ensure_unique_database(database_id, database)
        if not self._set_archived(database, archived, expected_revision, actor):
            return None
        self._record(audit, actor)
        return self.get_database(database_id)

    # ----------------------------------------------------------- consumers

    def list_consumers(self, *, database_id=None, service_id=None):
        rows = [
            c
            for c in self.consumers.values()
            if (database_id is None or c["database_instance_id"] == database_id)
            and (service_id is None or c["service_id"] == service_id)
        ]
        return [self._consumer_view(c) for c in rows]

    def get_consumer(self, consumer_id):
        consumer = self.consumers.get(consumer_id)
        return self._consumer_view(consumer) if consumer else None

    def insert_consumer(self, consumer_id, fields: ConsumerFields, actor, audit):
        self._active_or_raise(
            self.databases,
            fields.database_instance_id,
            "database_instance_id",
            "Instância",
            "database_instance_archived",
        )
        self._active_or_raise(self.services, fields.service_id, "service_id", "Serviço", "service_archived")
        for other in self.consumers.values():
            if (
                other["database_instance_id"] == fields.database_instance_id
                and other["service_id"] == fields.service_id
            ):
                raise ConflictError("database_consumer_exists", "duplicado")
        self.consumers[consumer_id] = {
            "id": consumer_id,
            "database_instance_id": fields.database_instance_id,
            "service_id": fields.service_id,
            "notes": fields.notes,
            "created_at": _now(),
            "created_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_consumer(consumer_id)

    def delete_consumer(self, consumer_id, actor, audit):
        if self.consumers.pop(consumer_id, None) is None:
            return False
        self._record(audit, actor)
        return True

    # ------------------------------------------------------------- history

    def list_subject_history(self, subject_id, limit):
        events = [
            e
            for e in self.servers_repo.audit
            if e["entity_id"] == subject_id or subject_id in e["subject_ids"]
        ]
        return list(reversed(events))[:limit]
