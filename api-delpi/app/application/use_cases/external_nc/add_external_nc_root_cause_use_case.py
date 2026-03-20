# app/application/use_cases/external_nc/add_external_nc_root_cause_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.add_external_nc_root_cause_request import (
    AddExternalNcRootCauseRequest,
)
from app.domain.entities.external_nc.external_nonconformity_root_cause import (
    ExternalNonconformityRootCause,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_root_cause_repository import (
    ExternalNonconformityRootCauseRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class AddExternalNcRootCauseUseCase:
    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        root_cause_repository: ExternalNonconformityRootCauseRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._root_cause_repository = root_cause_repository
        self._audit_event_repository = audit_event_repository

    def execute(
        self,
        request: AddExternalNcRootCauseRequest,
    ) -> ExternalNonconformityRootCause:
        self._validate_request(request)

        nonconformity = self._nonconformity_repository.get_by_id(
            request.nonconformity_id.strip()
        )
        if nonconformity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        entity = ExternalNonconformityRootCause(
            id=str(uuid4()),
            nonconformity_id=nonconformity.id,
            analysis_method=self._normalize_optional_str(request.analysis_method),
            cause_dimension=self._normalize_optional_str(request.cause_dimension),
            category=self._normalize_optional_str(request.category),
            why_level=request.why_level,
            description=request.description.strip(),
            is_root_cause=request.is_root_cause,
            created_by_user_id=request.created_by_user_id.strip(),
            created_at=datetime.now(timezone.utc),
        )

        created = self._root_cause_repository.create(entity)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=nonconformity.id,
                event_type="root_cause_added",
                actor_user_id=request.created_by_user_id.strip(),
                payload_json={
                    "root_cause_id": created.id,
                    "analysis_method": created.analysis_method,
                    "cause_dimension": created.cause_dimension,
                    "category": created.category,
                    "why_level": created.why_level,
                    "is_root_cause": created.is_root_cause,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return created

    def _validate_request(self, request: AddExternalNcRootCauseRequest) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        if not request.description or not request.description.strip():
            raise ValueError("description é obrigatório.")

        if not request.created_by_user_id or not request.created_by_user_id.strip():
            raise ValueError("created_by_user_id é obrigatório.")

        if request.why_level is not None and not (1 <= request.why_level <= 10):
            raise ValueError("why_level deve estar entre 1 e 10.")

    def _normalize_optional_str(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None