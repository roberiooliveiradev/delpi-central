"""Casos de uso de redes e da conectividade servidor ↔ rede (E2B)."""

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
    NETWORK_SORT_KEYS,
    Actor,
    AuditEvent,
    ConnectivityRepository,
    InventoryRepository,
    ItPortalRepository,
    NetworkQuery,
)
from it_portal_app.application.service_inventory import server_archived_error
from it_portal_app.domain.catalogs import (
    CRITICALITIES,
    ENVIRONMENTS,
    NETWORK_SCOPES,
    UNIT_CODES,
)
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.domain.networks import (
    NETWORK_FIELD_NAMES,
    address_in_network,
    build_network_fields,
    build_server_network_link_fields,
    validate_link_address,
)
from it_portal_app.domain.servers import diff_fields


def network_archived_error() -> ConflictError:
    return ConflictError(
        "network_archived", "Rede arquivada: restaure o cadastro antes de alterá-la."
    )


def network_links_outside_cidr_error() -> ConflictError:
    return ConflictError(
        "network_links_outside_cidr",
        "Há servidores vinculados com IP fora do novo CIDR. Ajuste ou remova esses "
        "vínculos antes de alterar o endereço da rede.",
        {"fields": {"cidr": "Servidores vinculados usam IPs fora deste CIDR."}},
    )


class NetworkInventory:
    def __init__(
        self,
        connectivity: ConnectivityRepository,
        inventory: InventoryRepository,
        servers: ItPortalRepository,
    ):
        self._repo = connectivity
        self._inventory = inventory
        self._servers = servers

    # ------------------------------------------------------------- networks

    def list_networks(self, query: NetworkQuery) -> dict:
        normalized = normalize_listing(
            query,
            sort_keys=NETWORK_SORT_KEYS,
            choices={
                "unit_code": UNIT_CODES,
                "environment": ENVIRONMENTS,
                "network_scope": NETWORK_SCOPES,
                "criticality": CRITICALITIES,
            },
        )
        items, total = self._repo.list_networks(normalized)
        return page_result(items, total, normalized)

    def get_network(self, network_id: str) -> dict:
        network = self._repo.get_network(network_id)
        if network is None:
            raise NotFoundError("network_not_found", "Rede não encontrada.")
        return network

    def create_network(self, raw: dict, actor: Actor) -> dict:
        fields = build_network_fields(raw)
        network_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="network",
            entity_id=network_id,
            server_id=None,
            event_type="network_created",
            changes={"fields": fields.as_dict()},
            subject_ids=(network_id,),
        )
        return self._repo.insert_network(network_id, fields, actor, audit)

    def update_network(
        self, network_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(network_id)
        fields = build_network_fields(raw)
        changes = diff_fields(current, fields.as_dict(), NETWORK_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise revision_conflict()
            return current
        if "cidr" in changes:
            links = self._repo.list_network_links(network_id=network_id)
            if any(
                link["ip_address"] and not address_in_network(link["ip_address"], fields.cidr)
                for link in links
            ):
                raise network_links_outside_cidr_error()
        audit = AuditEvent(
            entity_type="network",
            entity_id=network_id,
            server_id=None,
            event_type="network_updated",
            changes=changes,
            subject_ids=(network_id,),
        )
        updated = self._repo.update_network(network_id, fields, expected_revision, actor, audit)
        if updated is None:
            raise revision_conflict()
        return updated

    def archive_network(self, network_id: str, expected_revision: int, actor: Actor) -> dict:
        self._require_active(network_id)
        return self._set_archived(network_id, True, expected_revision, actor)

    def restore_network(self, network_id: str, expected_revision: int, actor: Actor) -> dict:
        current = self.get_network(network_id)
        if not current["archived"]:
            raise ConflictError("network_not_archived", "A rede já está ativa.")
        return self._set_archived(network_id, False, expected_revision, actor)

    def list_history(self, network_id: str) -> list[dict]:
        self.get_network(network_id)
        return self._inventory.list_subject_history(network_id, HISTORY_LIMIT)

    # ---------------------------------------------------------- connectivity

    def list_network_servers(self, network_id: str) -> list[dict]:
        self.get_network(network_id)
        return self._repo.list_network_links(network_id=network_id)

    def list_server_networks(self, server_id: str) -> list[dict]:
        if self._servers.get_server(server_id) is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return self._repo.list_network_links(server_id=server_id)

    def link_server_to_network(self, raw: dict, actor: Actor) -> dict:
        fields = build_server_network_link_fields(raw)
        server = self._servers.get_server(fields.server_id)
        if server is None:
            raise reference_not_found("server_id", "Servidor não encontrado.")
        network = self._repo.get_network(fields.network_id)
        if network is None:
            raise reference_not_found("network_id", "Rede não encontrada.")
        if server["archived"]:
            raise server_archived_error()
        if network["archived"]:
            raise network_archived_error()
        validate_link_address(fields.ip_address, network["cidr"])
        link_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="server_network_link",
            entity_id=link_id,
            server_id=server["id"],
            event_type="server_network_link_created",
            changes=_link_snapshot(server, network, fields.ip_address),
            subject_ids=(server["id"], network["id"]),
        )
        return self._repo.insert_network_link(link_id, fields, actor, audit)

    def unlink_server_from_network(self, link_id: str, actor: Actor) -> None:
        link = self._repo.get_network_link(link_id)
        if link is None:
            raise NotFoundError("server_network_link_not_found", "Vínculo não encontrado.")
        audit = AuditEvent(
            entity_type="server_network_link",
            entity_id=link_id,
            server_id=link["server_id"],
            event_type="server_network_link_removed",
            changes=_link_snapshot(link["server"], link["network"], link["ip_address"]),
            subject_ids=(link["server_id"], link["network_id"]),
        )
        if not self._repo.delete_network_link(link_id, actor, audit):
            raise NotFoundError("server_network_link_not_found", "Vínculo não encontrado.")

    # -------------------------------------------------------------- helpers

    def _require_active(self, network_id: str) -> dict:
        network = self.get_network(network_id)
        if network["archived"]:
            raise network_archived_error()
        return network

    def _set_archived(
        self, network_id: str, archived: bool, expected_revision: int, actor: Actor
    ) -> dict:
        audit = AuditEvent(
            entity_type="network",
            entity_id=network_id,
            server_id=None,
            event_type="network_archived" if archived else "network_restored",
            subject_ids=(network_id,),
        )
        updated = self._repo.set_network_archived(
            network_id, archived, expected_revision, actor, audit
        )
        if updated is None:
            raise revision_conflict()
        return updated


def _link_snapshot(server: dict, network: dict, ip_address: str | None) -> dict:
    return {
        "server": {"id": server["id"], "code": server["code"], "name": server["name"]},
        "network": {
            "id": network["id"],
            "code": network["code"],
            "name": network["name"],
            "cidr": network["cidr"],
        },
        "ip_address": ip_address,
    }
