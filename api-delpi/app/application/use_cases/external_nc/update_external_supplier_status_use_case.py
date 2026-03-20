# app/application/use_cases/external_nc/update_external_supplier_status_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.update_external_supplier_status_request import (
    UpdateExternalSupplierStatusRequest,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class UpdateExternalSupplierStatusUseCase:
    _ALLOWED_SUPPLIER_STATUS = {
        "not-requested",
        "awaiting-supplier",
        "supplier-responded",
        "supplier-action-pending",
        "supplier-validated",
        "supplier-overdue",
    }

    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._audit_event_repository = audit_event_repository

    def execute(
        self,
        request: UpdateExternalSupplierStatusRequest,
    ):
        self._validate_request(request)

        nc = self._nonconformity_repository.get_by_id(request.nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade externa não encontrada.")

        previous_supplier_status = nc.supplier_status
        new_supplier_status = request.supplier_status.strip()

        if previous_supplier_status == new_supplier_status:
            return nc

        nc.supplier_status = new_supplier_status
        updated = self._nonconformity_repository.update(nc)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=updated.id,
                event_type="supplier_status_updated",
                actor_user_id=request.actor_user_id.strip(),
                payload_json={
                    "from_supplier_status": previous_supplier_status,
                    "to_supplier_status": new_supplier_status,
                    "justification": self._normalize(request.justification),
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return updated

    def _validate_request(
        self,
        request: UpdateExternalSupplierStatusRequest,
    ) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        if not request.supplier_status or not request.supplier_status.strip():
            raise ValueError("supplier_status é obrigatório.")

        if not request.actor_user_id or not request.actor_user_id.strip():
            raise ValueError("actor_user_id é obrigatório.")

        normalized_status = request.supplier_status.strip()
        if normalized_status not in self._ALLOWED_SUPPLIER_STATUS:
            raise ValueError("supplier_status inválido.")

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None