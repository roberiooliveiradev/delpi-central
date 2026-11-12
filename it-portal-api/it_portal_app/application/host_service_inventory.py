"""Windows SCM inventory ingestion/queries (never issues service-control commands)."""
from __future__ import annotations

from it_portal_app.application.observation_service import (
    _allowlist_server_ids, _windows_collector_bindings,
)
from it_portal_app.application.ports import Actor
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.host_services import build_host_service_batch
from it_portal_app.domain.servers import normalize_hostname


class HostServiceInventory:
    def __init__(self, repository, servers):
        self.repository = repository
        self.servers = servers

    def _server(self, server_id: str) -> dict:
        server = self.servers.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return server

    def ingest(self, server_id: str, raw: dict, *, collector_client_id: str) -> dict:
        # Dedicated S2S scope is enforced at the HTTP boundary.
        if server_id not in _allowlist_server_ids() or server_id not in (
            _windows_collector_bindings().get(collector_client_id, frozenset())
        ):
            raise ConflictError("windows_service_inventory_forbidden", "Coletor não autorizado para este servidor.")
        server = self._server(server_id)
        if server.get("archived"):
            raise ConflictError("server_archived", "Servidor arquivado não aceita coleta.")
        batch = build_host_service_batch(raw)
        if normalize_hostname(server.get("hostname")) != batch.hostname:
            raise ValidationError("hostname_mismatch", "Hostname diferente do servidor cadastrado.")
        return self.repository.ingest_batch(server_id, collector_client_id, batch)

    def list_services(self, server_id: str, *, q: str | None, state: str | None,
                      start_mode: str | None, present: str, page: int, page_size: int, favorites_only: bool = False) -> dict:
        self._server(server_id)
        rows, total, current, favorites_count = self.repository.list_services(
            server_id, q=q, state=state, start_mode=start_mode,
            present=present, page=page, page_size=page_size, favorites_only=favorites_only,
        )
        return {"items": rows, "total": total, "page": page, "page_size": page_size,
                "current": current, "favorites_count": favorites_count}

    def save_preference(self, server_id: str, service_name: str, *,
                        is_favorite: bool, criticality: str, actor: Actor) -> dict:
        server = self._server(server_id)
        if server.get("archived"):
            raise ConflictError("server_archived", "Servidor arquivado não permite alterar favoritos.")
        if (not service_name or len(service_name) > 200 or
                any(ord(ch) < 32 or ch in "\\\\/" for ch in service_name)):
            raise ValidationError("invalid_service_name", "Nome do serviço inválido.")
        if not is_favorite and criticality != "normal":
            raise ValidationError("invalid_favorite_criticality", "Serviço não favorito deve ter criticidade normal.")
        key = service_name.casefold()
        if len(key) > 200:
            raise ValidationError("invalid_service_name", "Nome do serviço excede o limite.")
        preference = self.repository.save_preference(
            server_id, key, is_favorite=is_favorite,
            criticality=criticality, actor=actor,
        )
        if preference is None:
            raise NotFoundError("host_service_not_found", "Serviço Windows não encontrado neste servidor.")
        return preference
