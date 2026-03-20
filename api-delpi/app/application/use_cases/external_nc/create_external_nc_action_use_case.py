# app/application/use_cases/external_nc/create_external_nc_action_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.create_external_nc_action_request import (
    CreateExternalNcActionRequest,
)
from app.domain.entities.external_nc.external_nonconformity_action import (
    ExternalNonconformityAction,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nonconformity_action_repository import (
    ExternalNonconformityActionRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class CreateExternalNcActionUseCase:
    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        action_repository: ExternalNonconformityActionRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._action_repository = action_repository
        self._audit_event_repository = audit_event_repository

    def execute(
        self,
        request: CreateExternalNcActionRequest,
    ) -> ExternalNonconformityAction:
        self._validate_request(request)

        nc = self._nonconformity_repository.get_by_id(request.nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade externa não encontrada.")

        entity = ExternalNonconformityAction(
            id=str(uuid4()),
            nonconformity_id=nc.id,
            root_cause_id=self._normalize(request.root_cause_id),
            action_type=request.action_type.strip(),
            title=request.title.strip(),
            description=request.description.strip(),
            responsible_user_id=self._normalize(request.responsible_user_id),
            responsible_external_name=self._normalize(request.responsible_external_name),
            responsible_external_email=self._normalize(request.responsible_external_email),
            start_date=request.start_date,
            due_date=request.due_date,
            completed_at=None,
            status="pending",
            verification_required=request.verification_required,
            effectiveness_due_date=request.effectiveness_due_date,
            completion_notes=None,
            created_by_user_id=request.created_by_user_id.strip(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        created = self._action_repository.create(entity)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=nc.id,
                event_type="action_created",
                actor_user_id=request.created_by_user_id.strip(),
                payload_json={
                    "action_id": created.id,
                    "action_type": created.action_type,
                    "due_date": created.due_date,
                    "responsible_user_id": created.responsible_user_id,
                    "responsible_external_name": created.responsible_external_name,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return created

    def _validate_request(self, request: CreateExternalNcActionRequest) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")
        if not request.action_type or not request.action_type.strip():
            raise ValueError("action_type é obrigatório.")
        if not request.title or not request.title.strip():
            raise ValueError("title é obrigatório.")
        if not request.description or not request.description.strip():
            raise ValueError("description é obrigatório.")
        if not request.created_by_user_id or not request.created_by_user_id.strip():
            raise ValueError("created_by_user_id é obrigatório.")
        if request.start_date and request.start_date > request.due_date:
            raise ValueError("start_date não pode ser maior que due_date.")
        if request.effectiveness_due_date and request.effectiveness_due_date < request.due_date:
            raise ValueError("effectiveness_due_date não pode ser anterior a due_date.")
        if not self._has_responsible(
            request.responsible_user_id,
            request.responsible_external_name,
        ):
            raise ValueError("Ação exige responsável.")
        if request.due_date is None:
            raise ValueError("Ação exige prazo.")

    def _has_responsible(self, user_id: str | None, external_name: str | None) -> bool:
        return bool(self._normalize(user_id) or self._normalize(external_name))

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None