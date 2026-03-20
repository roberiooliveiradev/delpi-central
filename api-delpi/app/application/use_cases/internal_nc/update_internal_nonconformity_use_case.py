from __future__ import annotations

from app.application.dto.internal_nc.update_internal_nonconformity_request import (
    UpdateInternalNonconformityRequest,
)
from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class UpdateInternalNonconformityUseCase:
    def __init__(self, repository: InternalNonconformityRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: UpdateInternalNonconformityRequest,
    ) -> InternalNonconformity:
        current = self._repository.get_by_id(request.nonconformity_id.strip())
        if current is None:
            raise ValueError("Não conformidade interna não encontrada.")

        entity = InternalNonconformity(
            id=current.id,
            code=current.code,
            source_type=request.source_type.strip(),
            source_inspection_id=self._normalize(request.source_inspection_id),
            production_order=self._normalize(request.production_order),
            item_code=request.item_code.strip(),
            item_description=request.item_description.strip(),
            lot_number=self._normalize(request.lot_number),
            sector=request.sector.strip(),
            operation_code=self._normalize(request.operation_code),
            operation_description=self._normalize(request.operation_description),
            defect_category=request.defect_category.strip(),
            defect_description=request.defect_description.strip(),
            detected_by_user_id=request.detected_by_user_id.strip(),
            detection_date=request.detection_date,
            defective_quantity=request.defective_quantity,
            inspected_quantity=request.inspected_quantity,
            severity=request.severity.strip(),
            priority=request.priority.strip(),
            current_status=request.current_status.strip(),
            containment_action_summary=self._normalize(request.containment_action_summary),
            disposition_type=self._normalize(request.disposition_type),
            immediate_cause_notes=self._normalize(request.immediate_cause_notes),
            root_cause_summary=self._normalize(request.root_cause_summary),
            responsible_user_id=self._normalize(request.responsible_user_id),
            due_date=request.due_date,
            closed_at=current.closed_at,
            cancellation_reason=self._normalize(request.cancellation_reason),
            created_at=current.created_at,
            updated_at=current.updated_at,
        )
        return self._repository.update(entity)

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None