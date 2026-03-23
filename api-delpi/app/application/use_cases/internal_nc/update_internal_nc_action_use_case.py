from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.internal_nc.update_internal_nc_action_request import (
    UpdateInternalNcActionRequest,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.internal_nc.internal_nonconformity_action_repository import (
    InternalNonconformityActionRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class UpdateInternalNcActionUseCase:
    def __init__(
        self,
        action_repository: InternalNonconformityActionRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._action_repository = action_repository
        self._audit_event_repository = audit_event_repository

    def execute(self, request: UpdateInternalNcActionRequest):
        self._validate_request(request)

        current = self._action_repository.get_by_id(request.action_id.strip())
        if current is None:
            raise ValueError("Ação não encontrada.")

        current.root_cause_id = self._normalize(request.root_cause_id)
        current.action_type = request.action_type.strip()
        current.title = request.title.strip()
        current.description = request.description.strip()
        current.responsible_user_id = self._normalize(request.responsible_user_id)
        current.responsible_external_name = self._normalize(request.responsible_external_name)
        current.responsible_external_email = self._normalize(request.responsible_external_email)
        current.start_date = request.start_date
        current.due_date = request.due_date
        current.verification_required = request.verification_required
        current.effectiveness_due_date = request.effectiveness_due_date

        updated = self._action_repository.update(current)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="internal_nonconformity",
                entity_id=updated.nonconformity_id,
                event_type="action_updated",
                actor_user_id=None,
                payload_json={"action_id": updated.id},
                created_at=datetime.now(timezone.utc),
            )
        )

        return updated

    def _validate_request(self, request: UpdateInternalNcActionRequest) -> None:
        if not request.action_id or not request.action_id.strip():
            raise ValueError("action_id é obrigatório.")
        if not request.action_type or not request.action_type.strip():
            raise ValueError("action_type é obrigatório.")
        if not request.title or not request.title.strip():
            raise ValueError("title é obrigatório.")
        if not request.description or not request.description.strip():
            raise ValueError("description é obrigatório.")
        if request.start_date and request.start_date > request.due_date:
            raise ValueError("start_date não pode ser maior que due_date.")
        if request.effectiveness_due_date and request.effectiveness_due_date < request.due_date:
            raise ValueError("effectiveness_due_date não pode ser anterior a due_date.")
        if not (self._normalize(request.responsible_user_id) or self._normalize(request.responsible_external_name)):
            raise ValueError("Ação exige responsável.")

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None