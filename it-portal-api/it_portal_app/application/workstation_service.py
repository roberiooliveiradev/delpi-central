"""G1-API: casos de uso de computadores gerenciados (sem controle remoto)."""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Protocol

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.application.workstation_ports import (
    WORKSTATION_SORT_KEYS,
    WorkstationQuery,
    WorkstationRepository,
)
from it_portal_app.domain.catalogs import ADMINISTRATIVE_STATUSES, UNIT_CODES
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError, PersistenceUnavailableError
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


class OwnerResolver(Protocol):
    def resolve(self, user_id: str, access_token: str) -> str: ...


class WorkstationService:
    def __init__(self, repository: WorkstationRepository, owner_resolver: OwnerResolver | None = None):
        self._repository = repository
        self._owner_resolver = owner_resolver

    def _resolve_owner(self, fields, raw: dict, access_token: str, current: dict | None = None):
        """Somente novo vinculo exige Core; demais edicoes preservam snapshot vigente."""
        previous_id = current.get("responsible_user_id") if current else None
        if "responsible_user_id" not in raw and previous_id:
            # Clientes anteriores ao G1-OWNER nao podem apagar um vinculo existente.
            return replace(fields, responsible_user_id=previous_id, responsible=current["responsible"])
        user_id = fields.responsible_user_id
        if not user_id:
            # Desvinculacao explicita remove o snapshot; cadastros legados sem ID permanecem compativeis.
            if previous_id and "responsible_user_id" in raw:
                return replace(fields, responsible=None)
            return fields
        if user_id == previous_id:
            return replace(fields, responsible=current["responsible"])
        if self._owner_resolver is None:
            raise PersistenceUnavailableError("owner_directory_unavailable", "Diretorio de usuarios indisponivel.")
        owner_name = self._owner_resolver.resolve(user_id, access_token)
        return replace(fields, responsible=owner_name)


    def list_workstations(self, query: WorkstationQuery) -> dict:
        filters = normalize_workstation_query(query)
        items, total = self._repository.list_workstations(filters)
        return {"items": items, "total": total, "page": filters.page, "page_size": filters.page_size}

    def get_workstation(self, workstation_id: str) -> dict:
        result = self._repository.get_workstation(workstation_id)
        if result is None:
            raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
        return result

    def create_workstation(self, raw: dict, actor: Actor, access_token: str = "") -> dict:
        fields = self._resolve_owner(build_workstation_fields(raw), raw, access_token)
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

    def update_workstation(self, workstation_id: str, raw: dict, revision: int, actor: Actor, access_token: str = "") -> dict:
        current = self._require_active(workstation_id)
        fields = self._resolve_owner(build_workstation_fields(raw), raw, access_token, current)
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
