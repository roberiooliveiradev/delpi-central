"""G1-API: casos de uso de computadores gerenciados (sem controle remoto)."""

from __future__ import annotations

import uuid
from dataclasses import replace

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.application.workstation_ports import (
    WORKSTATION_SORT_KEYS,
    WorkstationQuery,
    WorkstationRepository,
)
from it_portal_app.domain.catalogs import ADMINISTRATIVE_STATUSES, UNIT_CODES
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.servers import diff_fields
from it_portal_app.domain.workstations import (
    DEVICE_KINDS,
    WORKSTATION_FIELD_NAMES,
    build_workstation_fields,
)

MAX_PAGE_SIZE = 100
HISTORY_LIMIT = 50
ARCHIVED_FILTERS = ("active", "archived", "all")


def revision_conflict() -> ConflictError:
    return ConflictError(
        "revision_conflict", "O cadastro foi alterado por outra pessoa. Recarregue e tente novamente."
    )


def normalize_workstation_query(query: WorkstationQuery) -> WorkstationQuery:
    errors: dict[str, str] = {}
    if query.unit_code and query.unit_code not in UNIT_CODES:
        errors["unit_code"] = "Unidade invalida."
    if query.device_kind and query.device_kind not in DEVICE_KINDS:
        errors["device_kind"] = "Tipo de computador invalido."
    if query.administrative_status and query.administrative_status not in ADMINISTRATIVE_STATUSES:
        errors["administrative_status"] = "Situacao invalida."
    if query.archived not in ARCHIVED_FILTERS:
        errors["archived"] = "Filtro de arquivamento invalido."
    if query.sort not in WORKSTATION_SORT_KEYS:
        errors["sort"] = "Ordenacao invalida."
    if query.direction not in ("asc", "desc"):
        errors["direction"] = "Direcao invalida."
    if errors:
        raise ValidationError("invalid_query", "Filtros invalidos.", {"fields": errors})
    text = (query.q or "").strip() or None
    return replace(
        query,
        q=text[:120] if text else None,
        page=max(1, query.page),
        page_size=min(MAX_PAGE_SIZE, max(1, query.page_size)),
    )


class WorkstationService:
    def __init__(self, repository: WorkstationRepository):
        self._repository = repository

    def list_workstations(self, query: WorkstationQuery) -> dict:
        filters = normalize_workstation_query(query)
        items, total = self._repository.list_workstations(filters)
        return {"items": items, "total": total, "page": filters.page, "page_size": filters.page_size}

    def get_workstation(self, workstation_id: str) -> dict:
        result = self._repository.get_workstation(workstation_id)
        if result is None:
            raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
        return result

    def create_workstation(self, raw: dict, actor: Actor) -> dict:
        fields = build_workstation_fields(raw)
        workstation_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="workstation",
            entity_id=workstation_id,
            server_id=None,
            event_type="workstation_created",
            changes={"fields": fields.as_dict()},
            subject_ids=(workstation_id,),
        )
        return self._repository.insert_workstation(workstation_id, fields, actor, audit)

    def update_workstation(self, workstation_id: str, raw: dict, revision: int, actor: Actor) -> dict:
        current = self._require_active(workstation_id)
        fields = build_workstation_fields(raw)
        changes = diff_fields(current, fields.as_dict(), WORKSTATION_FIELD_NAMES)
        if not changes:
            if current["revision"] != revision:
                raise revision_conflict()
            return current
        audit = AuditEvent(
            entity_type="workstation",
            entity_id=workstation_id,
            server_id=None,
            event_type="workstation_updated",
            changes=changes,
            subject_ids=(workstation_id,),
        )
        updated = self._repository.update_workstation(workstation_id, fields, revision, actor, audit)
        if updated is None:
            raise revision_conflict()
        return updated

    def archive_workstation(self, workstation_id: str, revision: int, actor: Actor) -> dict:
        self._require_active(workstation_id)
        audit = AuditEvent(
            entity_type="workstation", entity_id=workstation_id, server_id=None,
            event_type="workstation_archived", subject_ids=(workstation_id,),
        )
        result = self._repository.set_workstation_archived(
            workstation_id, True, revision, actor, audit
        )
        if result is None:
            raise revision_conflict()
        return result

    def restore_workstation(self, workstation_id: str, revision: int, actor: Actor) -> dict:
        current = self.get_workstation(workstation_id)
        if not current["archived"]:
            raise ConflictError("workstation_not_archived", "O computador ja esta ativo.")
        audit = AuditEvent(
            entity_type="workstation", entity_id=workstation_id, server_id=None,
            event_type="workstation_restored", subject_ids=(workstation_id,),
        )
        result = self._repository.set_workstation_archived(
            workstation_id, False, revision, actor, audit
        )
        if result is None:
            raise revision_conflict()
        return result

    def list_history(self, workstation_id: str) -> list[dict]:
        self.get_workstation(workstation_id)
        return self._repository.list_history(workstation_id, HISTORY_LIMIT)

    def _require_active(self, workstation_id: str) -> dict:
        current = self.get_workstation(workstation_id)
        if current["archived"]:
            raise ConflictError(
                "workstation_archived", "Computador arquivado: restaure o cadastro antes de editar."
            )
        return current
