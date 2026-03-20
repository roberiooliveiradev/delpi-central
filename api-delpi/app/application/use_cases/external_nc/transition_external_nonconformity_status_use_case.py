# app/application/use_cases/external_nc/transition_external_nonconformity_status_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.transition_external_nonconformity_status_request import (
    TransitionExternalNonconformityStatusRequest,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nonconformity_effectiveness_repository import (
    ExternalNonconformityEffectivenessRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_root_cause_repository import (
    ExternalNonconformityRootCauseRepositoryPort,
)


class TransitionExternalNonconformityStatusUseCase:
    _ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        "draft": {"open", "cancelled"},
        "open": {"under-triage", "cancelled"},
        "under-triage": {"containment-defined", "cancelled"},
        "containment-defined": {"under-investigation", "cancelled"},
        "under-investigation": {"action-plan-approved", "cancelled"},
        "action-plan-approved": {"in-progress", "cancelled"},
        "in-progress": {"pending-effectiveness-check", "cancelled"},
        "pending-effectiveness-check": {"closed", "cancelled"},
        "closed": {"reopened"},
        "cancelled": set(),
        "reopened": {"under-investigation", "cancelled"},
    }

    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
        effectiveness_repository: ExternalNonconformityEffectivenessRepositoryPort,
        root_cause_repository: ExternalNonconformityRootCauseRepositoryPort,
    ) -> None:
        self._repository = repository
        self._audit_event_repository = audit_event_repository
        self._effectiveness_repository = effectiveness_repository
        self._root_cause_repository = root_cause_repository

    def execute(
        self,
        request: TransitionExternalNonconformityStatusRequest,
    ):
        self._validate_request(request)

        entity = self._repository.get_by_id(request.nonconformity_id.strip())
        if entity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        current_status = entity.current_status
        target_status = request.target_status.strip()

        self._validate_transition(
            nonconformity_id=entity.id,
            current_status=current_status,
            target_status=target_status,
            justification=request.justification,
        )

        entity.current_status = target_status

        if target_status == "closed":
            entity.closed_at = datetime.now(timezone.utc)
            entity.cancellation_reason = None
        elif target_status == "cancelled":
            entity.cancellation_reason = self._normalize_optional_str(
                request.justification
            )
            entity.closed_at = None
        elif target_status == "reopened":
            entity.closed_at = None
            entity.cancellation_reason = None

        updated = self._repository.update(entity)

        latest_approved = None
        if target_status == "closed":
            latest_approved = self._effectiveness_repository.get_latest_approved_by_nonconformity_id(
                updated.id
            )

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=updated.id,
                event_type="status_transition",
                actor_user_id=request.actor_user_id.strip(),
                payload_json={
                    "from_status": current_status,
                    "to_status": target_status,
                    "justification": self._normalize_optional_str(request.justification),
                    "effectiveness_check_id": latest_approved.id if latest_approved else None,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return updated

    def _validate_request(
        self,
        request: TransitionExternalNonconformityStatusRequest,
    ) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        if not request.target_status or not request.target_status.strip():
            raise ValueError("target_status é obrigatório.")

        if not request.actor_user_id or not request.actor_user_id.strip():
            raise ValueError("actor_user_id é obrigatório.")

    def _validate_transition(
        self,
        *,
        nonconformity_id: str,
        current_status: str,
        target_status: str,
        justification: str | None,
    ) -> None:
        allowed = self._ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValueError(
                f"Transição inválida: {current_status} -> {target_status}."
            )

        if target_status == "action-plan-approved":
            has_root_cause = self._root_cause_repository.exists_for_nonconformity_id(
                nonconformity_id
            )
            if not has_root_cause:
                raise ValueError(
                    "Não é permitido aprovar plano sem causa raiz registrada."
                )

        if target_status == "closed":
            latest_approved = self._effectiveness_repository.get_latest_approved_by_nonconformity_id(
                nonconformity_id
            )
            if latest_approved is None:
                raise ValueError(
                    "Não é permitido encerrar sem validação de eficácia aprovada."
                )

        if target_status == "reopened":
            normalized = self._normalize_optional_str(justification)
            if not normalized:
                raise ValueError("Reabertura exige justificativa.")

        if target_status == "cancelled":
            normalized = self._normalize_optional_str(justification)
            if not normalized:
                raise ValueError("Cancelamento exige justificativa.")

    def _normalize_optional_str(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None