# app/application/use_cases/internal_nc/register_internal_nc_effectiveness_check_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.internal_nc.register_internal_nc_effectiveness_check_request import (
    RegisterInternalNcEffectivenessCheckRequest,
)
from app.domain.entities.internal_nc.internal_nonconformity_effectiveness_check import (
    InternalNonconformityEffectivenessCheck,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.internal_nc.internal_nonconformity_action_repository import (
    InternalNonconformityActionRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_effectiveness_repository import (
    InternalNonconformityEffectivenessRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class RegisterInternalNcEffectivenessCheckUseCase:
    _ALLOWED_RESULTS = {"approved", "rejected", "partially-approved", "pending"}

    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        effectiveness_repository: InternalNonconformityEffectivenessRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
        action_repository: InternalNonconformityActionRepositoryPort | None = None,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._effectiveness_repository = effectiveness_repository
        self._audit_event_repository = audit_event_repository
        self._action_repository = action_repository

    def execute(
        self,
        request: RegisterInternalNcEffectivenessCheckRequest,
    ) -> InternalNonconformityEffectivenessCheck:
        self._validate_request(request)

        nc = self._nonconformity_repository.get_by_id(request.nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        if request.action_id and self._action_repository is not None:
            action = self._action_repository.get_by_id(request.action_id.strip())
            if action is None:
                raise ValueError("Ação não encontrada.")
            if action.nonconformity_id != nc.id:
                raise ValueError("A ação informada não pertence à não conformidade.")

        entity = InternalNonconformityEffectivenessCheck(
            id=str(uuid4()),
            nonconformity_id=nc.id,
            action_id=request.action_id.strip() if request.action_id else None,
            checked_by_user_id=request.checked_by_user_id.strip(),
            checked_at=request.checked_at,
            criteria=request.criteria.strip(),
            result=request.result.strip(),
            notes=self._normalize(request.notes),
            next_action=self._normalize(request.next_action),
            created_at=datetime.now(timezone.utc),
        )

        created = self._effectiveness_repository.create(entity)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="internal_nonconformity",
                entity_id=nc.id,
                event_type="effectiveness_check_registered",
                actor_user_id=request.checked_by_user_id.strip(),
                payload_json={
                    "effectiveness_check_id": created.id,
                    "action_id": created.action_id,
                    "result": created.result,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        if created.result == "rejected":
            previous_status = nc.current_status
            nc.current_status = "reopened"
            nc.closed_at = None

            if created.next_action:
                nc.cancellation_reason = created.next_action

            self._nonconformity_repository.update(nc)

            self._audit_event_repository.create(
                NonconformityAuditEvent(
                    id=str(uuid4()),
                    entity_type="internal_nonconformity",
                    entity_id=nc.id,
                    event_type="reopened_by_effectiveness_rejection",
                    actor_user_id=request.checked_by_user_id.strip(),
                    payload_json={
                        "effectiveness_check_id": created.id,
                        "from_status": previous_status,
                        "to_status": "reopened",
                        "result": created.result,
                    },
                    created_at=datetime.now(timezone.utc),
                )
            )

        return created

    def _validate_request(
        self,
        request: RegisterInternalNcEffectivenessCheckRequest,
    ) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")
        if not request.checked_by_user_id or not request.checked_by_user_id.strip():
            raise ValueError("checked_by_user_id é obrigatório.")
        if not request.criteria or not request.criteria.strip():
            raise ValueError("criteria é obrigatório.")
        if not request.result or not request.result.strip():
            raise ValueError("result é obrigatório.")
        if request.result.strip() not in self._ALLOWED_RESULTS:
            raise ValueError("result inválido.")
        if request.checked_at is None:
            raise ValueError("checked_at é obrigatório.")

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None