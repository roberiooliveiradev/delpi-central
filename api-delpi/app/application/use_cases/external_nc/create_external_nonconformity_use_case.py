# app/application/use_cases/external_nc/create_external_nonconformity_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.create_external_nonconformity_request import (
    CreateExternalNonconformityRequest,
)
from app.domain.entities.external_nc.external_nonconformity import (
    ExternalNonconformity,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.sequential_code_generator import (
    SequentialCodeGeneratorPort,
)


class CreateExternalNonconformityUseCase:
    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
        sequential_code_generator: SequentialCodeGeneratorPort,
    ) -> None:
        self._repository = repository
        self._sequential_code_generator = sequential_code_generator

    def execute(
        self,
        request: CreateExternalNonconformityRequest,
    ) -> ExternalNonconformity:
        self._validate_request(request)

        now = datetime.now(timezone.utc)
        code = self._sequential_code_generator.next_code("external_nonconformity")

        entity = ExternalNonconformity(
            id=str(uuid4()),
            code=code,
            company_unit=request.company_unit.strip(),
            supplier_id=request.supplier_id,
            supplier_name_snapshot=request.supplier_name_snapshot.strip(),
            customer_name=self._normalize_optional_str(request.customer_name),
            origin_type=request.origin_type.strip(),
            source_channel=self._normalize_optional_str(request.source_channel),
            material_code=self._normalize_optional_str(request.material_code),
            material_description=self._normalize_optional_str(request.material_description),
            material_specification=self._normalize_optional_str(
                request.material_specification
            ),
            lot_number=self._normalize_optional_str(request.lot_number),
            purchase_order=self._normalize_optional_str(request.purchase_order),
            invoice_number=self._normalize_optional_str(request.invoice_number),
            document_reference=self._normalize_optional_str(request.document_reference),
            occurrence_date=request.occurrence_date,
            detection_date=request.detection_date,
            defective_quantity=request.defective_quantity,
            inspected_quantity=request.inspected_quantity,
            uom=self._normalize_optional_str(request.uom),
            severity=request.severity.strip(),
            priority=request.priority.strip(),
            occurrence_type=self._normalize_optional_str(request.occurrence_type),
            defect_category=self._normalize_optional_str(request.defect_category),
            recurrence_flag=request.recurrence_flag,
            containment_required=request.containment_required,
            title=request.title.strip(),
            problem_description=request.problem_description.strip(),
            business_impact=self._normalize_optional_str(request.business_impact),
            customer_impact=self._normalize_optional_str(request.customer_impact),
            production_impact=self._normalize_optional_str(request.production_impact),
            cost_estimate=request.cost_estimate,
            current_status="draft",
            supplier_status="not-requested",
            responsible_user_id=self._normalize_optional_str(request.responsible_user_id),
            opened_by_user_id=request.opened_by_user_id.strip(),
            due_date=request.due_date,
            closed_at=None,
            cancellation_reason=None,
            created_at=now,
            updated_at=now,
        )

        return self._repository.create(entity)

    def _validate_request(self, request: CreateExternalNonconformityRequest) -> None:
        if not request.company_unit or not request.company_unit.strip():
            raise ValueError("company_unit é obrigatório.")

        if not request.supplier_id or not request.supplier_id.strip():
            raise ValueError("supplier_id é obrigatório.")

        if (
            not request.supplier_name_snapshot
            or not request.supplier_name_snapshot.strip()
        ):
            raise ValueError("supplier_name_snapshot é obrigatório.")

        if not request.opened_by_user_id or not request.opened_by_user_id.strip():
            raise ValueError("opened_by_user_id é obrigatório.")

        if not request.title or not request.title.strip():
            raise ValueError("title é obrigatório.")

        if not request.problem_description or not request.problem_description.strip():
            raise ValueError("problem_description é obrigatório.")

        if request.defective_quantity < 0:
            raise ValueError("defective_quantity não pode ser negativo.")

        if (
            request.inspected_quantity is not None
            and request.inspected_quantity < 0
        ):
            raise ValueError("inspected_quantity não pode ser negativo.")

        if request.cost_estimate is not None and request.cost_estimate < 0:
            raise ValueError("cost_estimate não pode ser negativo.")

        if request.detection_date < request.occurrence_date:
            raise ValueError(
                "detection_date não pode ser anterior a occurrence_date."
            )

    def _normalize_optional_str(self, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None