from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.internal_nc.create_internal_nonconformity_request import (
    CreateInternalNonconformityRequest,
)
from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.sequential_code_generator import (
    SequentialCodeGeneratorPort,
)


class CreateInternalNonconformityUseCase:
    def __init__(
        self,
        repository: InternalNonconformityRepositoryPort,
        sequential_code_generator: SequentialCodeGeneratorPort,
    ) -> None:
        self._repository = repository
        self._sequential_code_generator = sequential_code_generator

    def execute(
        self,
        request: CreateInternalNonconformityRequest,
    ) -> InternalNonconformity:
        self._validate(request)

        now = datetime.now(timezone.utc)
        code = self._sequential_code_generator.next_code("internal_nonconformity")

        entity = InternalNonconformity(
            id=str(uuid4()),
            code=code,
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
            current_status="draft",
            containment_action_summary=self._normalize(request.containment_action_summary),
            disposition_type=self._normalize(request.disposition_type),
            immediate_cause_notes=self._normalize(request.immediate_cause_notes),
            root_cause_summary=self._normalize(request.root_cause_summary),
            responsible_user_id=self._normalize(request.responsible_user_id),
            due_date=request.due_date,
            closed_at=None,
            cancellation_reason=None,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(entity)

    def _validate(self, request: CreateInternalNonconformityRequest) -> None:
        if request.source_type.strip() not in {"manual", "inspection"}:
            raise ValueError("source_type inválido.")
        if not request.detected_by_user_id.strip():
            raise ValueError("detected_by_user_id é obrigatório.")
        if not request.item_code.strip():
            raise ValueError("item_code é obrigatório.")
        if not request.item_description.strip():
            raise ValueError("item_description é obrigatório.")
        if not request.sector.strip():
            raise ValueError("sector é obrigatório.")
        if not request.defect_category.strip():
            raise ValueError("defect_category é obrigatório.")
        if not request.defect_description.strip():
            raise ValueError("defect_description é obrigatório.")
        if request.defective_quantity < 0:
            raise ValueError("defective_quantity não pode ser negativo.")
        if request.inspected_quantity is not None and request.inspected_quantity < 0:
            raise ValueError("inspected_quantity não pode ser negativo.")

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None