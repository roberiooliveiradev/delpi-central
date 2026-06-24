from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.quality_action_plans.pac_quality_branch_service import (
    build_recurrence_key,
    validate_branch_code,
)


class QualityActionPlanRepository(Protocol):
    def create_plan(self, fields: dict[str, Any]) -> dict[str, Any]: ...

    def get_plan_by_id(self, plan_id: str) -> dict[str, Any] | None: ...

    def update_plan_status(
        self,
        plan_id: str,
        *,
        status: str,
        updated_by: str,
        comment: str | None = None,
    ) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class CreateQualityActionPlanRequest:
    title: str
    created_by_user_id: str
    customer_name: str | None = None
    customer_contact: str | None = None
    source_type: str | None = None
    source_reference: str | None = None
    product_code: str | None = None
    product_description: str | None = None
    batch_number: str | None = None
    reported_problem: str | None = None
    detected_at: str | None = None
    reported_at: str | None = None
    severity: str = "medium"
    status: str = "triage"
    owner_user_id: str | None = None
    branch_code: str | None = None
    department: str | None = None
    problem_category: str | None = None
    symptom_tags: list[str] | None = None
    root_cause_category: str | None = None
    failure_mode: str | None = None
    recurrence_key: str | None = None


class CreateQualityActionPlanUseCase:
    def __init__(self, repository: QualityActionPlanRepository) -> None:
        self._repository = repository

    def execute(self, request: CreateQualityActionPlanRequest) -> dict[str, Any]:
        if not request.title.strip():
            raise ValueError("title é obrigatório.")

        branch_code = validate_branch_code(request.branch_code, required=True)
        recurrence_key = build_recurrence_key(
            branch_code=branch_code,
            product_code=request.product_code,
            failure_mode=request.failure_mode,
            explicit=request.recurrence_key,
        )

        return self._repository.create_plan(
            {
                "title": request.title.strip(),
                "created_by_user_id": request.created_by_user_id,
                "customer_name": request.customer_name,
                "customer_contact": request.customer_contact,
                "source_type": request.source_type,
                "source_reference": request.source_reference,
                "product_code": request.product_code,
                "product_description": request.product_description,
                "batch_number": request.batch_number,
                "reported_problem": request.reported_problem,
                "detected_at": request.detected_at,
                "reported_at": request.reported_at,
                "severity": request.severity,
                "status": request.status,
                "owner_user_id": request.owner_user_id,
                "branch_code": branch_code,
                "department": request.department,
                "problem_category": request.problem_category,
                "symptom_tags": request.symptom_tags,
                "root_cause_category": request.root_cause_category,
                "failure_mode": request.failure_mode,
                "recurrence_key": recurrence_key,
            }
        )


class UpdateQualityActionPlanStatusUseCase:
    VALID_STATUSES = {
        "draft",
        "triage",
        "containment",
        "root_cause_analysis",
        "action_plan_defined",
        "in_progress",
        "waiting_validation",
        "completed",
        "cancelled",
    }

    def __init__(self, repository: QualityActionPlanRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        *,
        status: str,
        updated_by: str,
        comment: str | None = None,
    ) -> dict[str, Any] | None:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"status inválido: {status}")
        return self._repository.update_plan_status(
            plan_id,
            status=status,
            updated_by=updated_by,
            comment=comment,
        )
