from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.internal_nc.complete_internal_nc_action_request import (
    CompleteInternalNcActionRequest,
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


class CompleteInternalNcActionUseCase:
    def __init__(
        self,
        action_repository: InternalNonconformityActionRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._action_repository = action_repository
        self._audit_event_repository = audit_event_repository

    def execute(self, request: CompleteInternalNcActionRequest):
        if not request.action_id or not request.action_id.strip():
            raise ValueError("action_id é obrigatório.")
        if not request.actor_user_id or not request.actor_user_id.strip():
            raise ValueError("actor_user_id é obrigatório.")

        action = self._action_repository.get_by_id(request.action_id.strip())
        if action is None:
            raise ValueError("Ação não encontrada.")

        if not (action.responsible_user_id or action.responsible_external_name):
            raise ValueError("Não concluir ação sem responsável.")
        if action.due_date is None:
            raise ValueError("Não concluir ação sem prazo.")

        action.status = "completed"
        action.completed_at = datetime.now(timezone.utc)
        action.completion_notes = (
            request.completion_notes.strip()
            if request.completion_notes and request.completion_notes.strip()
            else None
        )

        updated = self._action_repository.update(action)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="internal_nonconformity",
                entity_id=updated.nonconformity_id,
                event_type="action_completed",
                actor_user_id=request.actor_user_id.strip(),
                payload_json={
                    "action_id": updated.id,
                    "completed_at": updated.completed_at,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return updated