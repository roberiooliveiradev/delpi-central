"""Repositório E2B em memória — exclusivo de testes de serviço/HTTP.

Compartilha servidores, serviços e auditoria com os fakes E1/E2A e reproduz as
garantias observáveis do adapter Postgres (unicidade ativa, pares únicos,
referência ativa, revisão otimista, IP dentro do CIDR). A paridade real é
coberta por `test_postgres_connectivity.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from it_portal_app.application.network_inventory import network_links_outside_cidr_error
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.integrations import format_integration_code
from it_portal_app.domain.networks import (
    address_in_network,
    format_network_code,
    validate_link_address,
)

from tests.inventory_fakes import InMemoryInventoryRepository, _server_summary


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InMemoryConnectivityRepository:
    inventory: InMemoryInventoryRepository
    networks: dict[str, dict] = field(default_factory=dict)
    links: dict[str, dict] = field(default_factory=dict)
    integrations: dict[str, dict] = field(default_factory=dict)
    dependencies: dict[str, dict] = field(default_factory=dict)
    _network_seq: int = 0
    _integration_seq: int = 0

    @property
    def _servers(self) -> dict:
        return self.inventory.servers_repo.servers

    def _record(self, audit, actor) -> None:
        self.inventory._record(audit, actor)

    def _new_versioned(self, values: dict, row_id: str, seq: int, code: str, actor) -> dict:
        now = _now()
        return {
            **values,
            "id": row_id,
            "seq": seq,
            "code": code,
            "revision": 1,
            "archived": False,
            "archived_at": None,
            "archived_by_name": None,
            "created_at": now,
            "created_by_name": actor.name,
            "updated_at": now,
            "updated_by_name": actor.name,
        }

    def _active_service(self, service_id: str, field_name: str) -> None:
        self.inventory._active_or_raise(
            self.inventory.services, service_id, field_name, "Serviço", "service_archived"
        )

    # ------------------------------------------------------------- networks

    def _network_view(self, network: dict) -> dict:
        return {
            **network,
            "server_count": sum(1 for l in self.links.values() if l["network_id"] == network["id"]),
        }

    def _network_summary(self, network_id: str) -> dict:
        network = self.networks[network_id]
        return {
            key: network[key]
            for key in (
                "id", "code", "name", "cidr", "vlan_id", "network_scope", "environment",
                "unit_code", "archived",
            )
        }

    def _ensure_unique_network(self, network_id: str, values: dict) -> None:
        for other in self.networks.values():
            if other["id"] == network_id or other["archived"]:
                continue
            if other["unit_code"] != values["unit_code"]:
                continue
            if other["name"].lower() == values["name"].lower():
                raise ConflictError("network_name_conflict", "duplicado")
            if (
                values["network_scope"] == "corporate"
                and other["network_scope"] == "corporate"
                and other["cidr"] == values["cidr"]
            ):
                raise ConflictError("network_cidr_conflict", "duplicado")

    def list_networks(self, query):
        items = self.inventory._archived_filter(list(self.networks.values()), query.archived)
        if query.q:
            needle = query.q.lower()
            items = [
                n
                for n in items
                if any(needle in (n[key] or "").lower() for key in ("name", "cidr", "zone", "location"))
            ]
        for column in ("unit_code", "environment", "network_scope", "criticality"):
            value = getattr(query, column)
            if value:
                items = [n for n in items if n[column] == value]
        page, total = self.inventory._page(items, query)
        return [self._network_view(n) for n in page], total

    def get_network(self, network_id):
        network = self.networks.get(network_id)
        return self._network_view(network) if network else None

    def insert_network(self, network_id, fields, actor, audit):
        values = fields.as_dict()
        self._ensure_unique_network(network_id, values)
        self._network_seq += 1
        self.networks[network_id] = self._new_versioned(
            values, network_id, self._network_seq, format_network_code(self._network_seq), actor
        )
        self._record(audit, actor)
        return self.get_network(network_id)

    def update_network(self, network_id, fields, expected_revision, actor, audit):
        network = self.networks[network_id]
        if network["revision"] != expected_revision or network["archived"]:
            return None
        values = fields.as_dict()
        if values["cidr"] != network["cidr"] and any(
            l["network_id"] == network_id
            and l["ip_address"]
            and not address_in_network(l["ip_address"], values["cidr"])
            for l in self.links.values()
        ):
            raise network_links_outside_cidr_error()
        self._ensure_unique_network(network_id, values)
        network.update(values)
        network.update(revision=network["revision"] + 1, updated_at=_now(), updated_by_name=actor.name)
        self._record(audit, actor)
        return self.get_network(network_id)

    def set_network_archived(self, network_id, archived, expected_revision, actor, audit):
        network = self.networks[network_id]
        if not archived and network["archived"]:
            self._ensure_unique_network(network_id, network)
        if not self.inventory._set_archived(network, archived, expected_revision, actor):
            return None
        self._record(audit, actor)
        return self.get_network(network_id)

    # ---------------------------------------------------------- connectivity

    def _link_view(self, link: dict) -> dict:
        return {
            **link,
            "server": _server_summary(self._servers[link["server_id"]]),
            "network": self._network_summary(link["network_id"]),
        }

    def list_network_links(self, *, network_id=None, server_id=None):
        rows = [
            l
            for l in self.links.values()
            if (network_id is None or l["network_id"] == network_id)
            and (server_id is None or l["server_id"] == server_id)
        ]
        return [self._link_view(l) for l in rows]

    def get_network_link(self, link_id):
        link = self.links.get(link_id)
        return self._link_view(link) if link else None

    def insert_network_link(self, link_id, fields, actor, audit):
        self.inventory._active_or_raise(
            self._servers, fields.server_id, "server_id", "Servidor", "server_archived"
        )
        self.inventory._active_or_raise(
            self.networks, fields.network_id, "network_id", "Rede", "network_archived"
        )
        validate_link_address(fields.ip_address, self.networks[fields.network_id]["cidr"])
        for other in self.links.values():
            if other["server_id"] == fields.server_id and other["network_id"] == fields.network_id:
                raise ConflictError("server_network_link_exists", "duplicado")
        self.links[link_id] = {
            "id": link_id,
            "server_id": fields.server_id,
            "network_id": fields.network_id,
            "ip_address": fields.ip_address,
            "interface_name": fields.interface_name,
            "notes": fields.notes,
            "created_at": _now(),
            "created_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_network_link(link_id)

    def delete_network_link(self, link_id, actor, audit):
        if self.links.pop(link_id, None) is None:
            return False
        self._record(audit, actor)
        return True

    # --------------------------------------------------------- integrations

    def _summary_or_none(self, service_id):
        return self.inventory._service_summary(service_id) if service_id else None

    def _integration_view(self, integration: dict) -> dict:
        return {
            **integration,
            "source_service": self._summary_or_none(integration["source_service_id"]),
            "target_service": self._summary_or_none(integration["target_service_id"]),
        }

    @staticmethod
    def _endpoint_key(values: dict, side: str) -> str:
        service_id = values[f"{side}_service_id"]
        return service_id or "external:" + values[f"{side}_external_name"].lower()

    def _ensure_unique_integration(self, integration_id: str, values: dict) -> None:
        key = (
            self._endpoint_key(values, "source"),
            self._endpoint_key(values, "target"),
            values["protocol"],
        )
        for other in self.integrations.values():
            if other["id"] == integration_id or other["archived"]:
                continue
            other_key = (
                self._endpoint_key(other, "source"),
                self._endpoint_key(other, "target"),
                other["protocol"],
            )
            if other_key == key:
                raise ConflictError("integration_exists", "duplicado")

    def _service_names(self, integration: dict) -> list[str]:
        names = [integration["name"]]
        for side in ("source", "target"):
            service_id = integration[f"{side}_service_id"]
            if service_id:
                names.append(self.inventory.services[service_id]["name"])
            else:
                names.append(integration[f"{side}_external_name"])
        return names

    def list_integrations(self, query):
        items = self.inventory._archived_filter(list(self.integrations.values()), query.archived)
        if query.q:
            needle = query.q.lower()
            items = [
                i for i in items if any(needle in name.lower() for name in self._service_names(i))
            ]
        if query.service_id:
            items = [
                i
                for i in items
                if query.service_id in (i["source_service_id"], i["target_service_id"])
            ]
        for column in ("protocol", "criticality", "administrative_status"):
            value = getattr(query, column)
            if value:
                items = [i for i in items if i[column] == value]
        page, total = self.inventory._page(items, query)
        return [self._integration_view(i) for i in page], total

    def get_integration(self, integration_id):
        integration = self.integrations.get(integration_id)
        return self._integration_view(integration) if integration else None

    def list_server_integrations(self, server_id):
        hosted = {
            h["service_id"] for h in self.inventory.hostings.values() if h["server_id"] == server_id
        }
        rows = [
            i
            for i in self.integrations.values()
            if i["source_service_id"] in hosted or i["target_service_id"] in hosted
        ]
        rows.sort(key=lambda i: (i["name"].lower(), i["seq"]))
        return [self._integration_view(i) for i in rows]

    def insert_integration(self, integration_id, fields, actor, audit):
        for side in ("source", "target"):
            service_id = getattr(fields, f"{side}_service_id")
            if service_id:
                self._active_service(service_id, f"{side}_service_id")
        values = fields.as_dict()
        self._ensure_unique_integration(integration_id, values)
        self._integration_seq += 1
        self.integrations[integration_id] = self._new_versioned(
            values,
            integration_id,
            self._integration_seq,
            format_integration_code(self._integration_seq),
            actor,
        )
        self._record(audit, actor)
        return self.get_integration(integration_id)

    def update_integration(self, integration_id, fields, expected_revision, actor, audit):
        integration = self.integrations[integration_id]
        if integration["revision"] != expected_revision or integration["archived"]:
            return None
        previous = {integration["source_service_id"], integration["target_service_id"]}
        for side in ("source", "target"):
            service_id = getattr(fields, f"{side}_service_id")
            if service_id and service_id not in previous:
                self._active_service(service_id, f"{side}_service_id")
        values = fields.as_dict()
        self._ensure_unique_integration(integration_id, values)
        integration.update(values)
        integration.update(
            revision=integration["revision"] + 1, updated_at=_now(), updated_by_name=actor.name
        )
        self._record(audit, actor)
        return self.get_integration(integration_id)

    def set_integration_archived(self, integration_id, archived, expected_revision, actor, audit):
        integration = self.integrations[integration_id]
        if not archived and integration["archived"]:
            self._ensure_unique_integration(integration_id, integration)
        if not self.inventory._set_archived(integration, archived, expected_revision, actor):
            return None
        self._record(audit, actor)
        return self.get_integration(integration_id)

    # --------------------------------------------------------- dependencies

    def _dependency_view(self, dependency: dict) -> dict:
        return {
            **dependency,
            "dependent_service": self.inventory._service_summary(dependency["dependent_service_id"]),
            "required_service": self.inventory._service_summary(dependency["required_service_id"]),
        }

    def list_dependencies(self, service_id):
        rows = [
            d
            for d in self.dependencies.values()
            if service_id in (d["dependent_service_id"], d["required_service_id"])
        ]
        return [self._dependency_view(d) for d in rows]

    def get_dependency(self, dependency_id):
        dependency = self.dependencies.get(dependency_id)
        return self._dependency_view(dependency) if dependency else None

    def insert_dependency(self, dependency_id, fields, actor, audit):
        self._active_service(fields.dependent_service_id, "dependent_service_id")
        self._active_service(fields.required_service_id, "required_service_id")
        for other in self.dependencies.values():
            if (
                other["dependent_service_id"] == fields.dependent_service_id
                and other["required_service_id"] == fields.required_service_id
            ):
                raise ConflictError("service_dependency_exists", "duplicado")
        self.dependencies[dependency_id] = {
            "id": dependency_id,
            "dependent_service_id": fields.dependent_service_id,
            "required_service_id": fields.required_service_id,
            "notes": fields.notes,
            "created_at": _now(),
            "created_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_dependency(dependency_id)

    def delete_dependency(self, dependency_id, actor, audit):
        if self.dependencies.pop(dependency_id, None) is None:
            return False
        self._record(audit, actor)
        return True
