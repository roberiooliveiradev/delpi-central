"""Casos de uso do cadastro de servidores e notas técnicas."""

from __future__ import annotations

import uuid
from dataclasses import replace

from it_portal_app.application.ports import (
    SERVER_SORT_KEYS,
    Actor,
    AuditEvent,
    ItPortalRepository,
    ServerQuery,
)
from it_portal_app.domain.catalogs import CRITICALITIES, ENVIRONMENTS, UNIT_CODES
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.notes import build_note_body
from it_portal_app.domain.servers import (
    SERVER_FIELD_NAMES,
    build_server_fields,
    diff_fields,
)

MAX_PAGE_SIZE = 100
HISTORY_LIMIT = 50
ARCHIVE_FILTERS = ("active", "archived", "all")


def _revision_conflict() -> ConflictError:
    return ConflictError(
        "revision_conflict",
        "O registro foi alterado por outra pessoa. Recarregue e tente novamente.",
    )


def normalize_server_query(query: ServerQuery) -> ServerQuery:
    errors: dict[str, str] = {}
    if query.unit_code and query.unit_code not in UNIT_CODES:
        errors["unit_code"] = "Unidade inválida."
    if query.environment and query.environment not in ENVIRONMENTS:
        errors["environment"] = "Ambiente inválido."
    if query.criticality and query.criticality not in CRITICALITIES:
        errors["criticality"] = "Criticidade inválida."
    if query.archived not in ARCHIVE_FILTERS:
        errors["archived"] = "Filtro de arquivamento inválido."
    if query.sort not in SERVER_SORT_KEYS:
        errors["sort"] = "Ordenação inválida."
    if query.direction not in ("asc", "desc"):
        errors["direction"] = "Direção inválida."
    if errors:
        raise ValidationError("invalid_query", "Filtros inválidos.", {"fields": errors})
    q = (query.q or "").strip() or None
    return replace(
        query,
        q=q[:120] if q else None,
        page=max(1, query.page),
        page_size=min(MAX_PAGE_SIZE, max(1, query.page_size)),
    )


class ServerService:
    def __init__(self, repository: ItPortalRepository):
        self._repo = repository

    def list_servers(self, query: ServerQuery) -> dict:
        normalized = normalize_server_query(query)
        items, total = self._repo.list_servers(normalized)
        return {
            "items": items,
            "total": total,
            "page": normalized.page,
            "page_size": normalized.page_size,
        }

    def get_server(self, server_id: str) -> dict:
        server = self._repo.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        return server

    def create_server(self, raw: dict, actor: Actor) -> dict:
        fields = build_server_fields(raw)
        server_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="server",
            entity_id=server_id,
            server_id=server_id,
            event_type="server_created",
            changes={"fields": fields.as_dict()},
        )
        return self._repo.insert_server(server_id, fields, actor, audit)

    def update_server(
        self, server_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self._require_active(server_id)
        fields = build_server_fields(raw)
        changes = diff_fields(current, fields.as_dict(), SERVER_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise _revision_conflict()
            return current
        audit = AuditEvent(
            entity_type="server",
            entity_id=server_id,
            server_id=server_id,
            event_type="server_updated",
            changes=changes,
        )
        updated = self._repo.update_server(
            server_id, fields, expected_revision, actor, audit
        )
        if updated is None:
            raise _revision_conflict()
        return updated

    def archive_server(self, server_id: str, expected_revision: int, actor: Actor) -> dict:
        self._require_active(server_id)
        open_actions = self._repo.count_open_action_plans(server_id)
        if open_actions:
            raise ConflictError(
                "server_has_open_action_plans",
                "Conclua ou cancele os planos de ação abertos antes de arquivar "
                "este servidor.",
                {"open_action_plans": open_actions},
            )
        audit = AuditEvent(
            entity_type="server",
            entity_id=server_id,
            server_id=server_id,
            event_type="server_archived",
        )
        updated = self._repo.set_server_archived(
            server_id, True, expected_revision, actor, audit
        )
        if updated is None:
            raise _revision_conflict()
        return updated

    def restore_server(self, server_id: str, expected_revision: int, actor: Actor) -> dict:
        current = self.get_server(server_id)
        if not current["archived"]:
            raise ConflictError("server_not_archived", "O servidor já está ativo.")
        audit = AuditEvent(
            entity_type="server",
            entity_id=server_id,
            server_id=server_id,
            event_type="server_restored",
        )
        updated = self._repo.set_server_archived(
            server_id, False, expected_revision, actor, audit
        )
        if updated is None:
            raise _revision_conflict()
        return updated

    def list_notes(self, server_id: str) -> list[dict]:
        self.get_server(server_id)
        return self._repo.list_notes(server_id)

    def add_note(self, server_id: str, raw_body: object, actor: Actor) -> dict:
        self._require_active(server_id)
        body = build_note_body(raw_body)
        note_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="server_note",
            entity_id=note_id,
            server_id=server_id,
            event_type="note_added",
        )
        return self._repo.insert_note(note_id, server_id, body, actor, audit)

    def list_history(self, server_id: str) -> list[dict]:
        self.get_server(server_id)
        return self._repo.list_server_history(server_id, HISTORY_LIMIT)

    def _require_active(self, server_id: str) -> dict:
        server = self.get_server(server_id)
        if server["archived"]:
            raise ConflictError(
                "server_archived",
                "Servidor arquivado: restaure o cadastro antes de alterá-lo.",
            )
        return server
