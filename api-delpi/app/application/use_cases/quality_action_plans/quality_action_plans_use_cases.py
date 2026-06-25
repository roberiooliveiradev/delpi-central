from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.quality_action_plans.pac_quality_branch_service import (
    build_recurrence_key,
    validate_branch_code,
)
from app.domain.services.quality_action_plans.pac_quality_nonconformity_scope_service import (
    validate_nonconformity_scope,
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

    def update_plan(self, plan_id: str, fields: dict[str, Any]) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class CreateQualityActionPlanRequest:
    title: str
    created_by_user_id: str
    customer_name: str | None = None
    customer_contact: str | None = None
    nonconformity_scope: str | None = None
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
    def __init__(
        self,
        repository: QualityActionPlanRepository,
        intelligence_sync: Any | None = None,
    ) -> None:
        self._repository = repository
        self._intelligence_sync = intelligence_sync

    def execute(self, request: CreateQualityActionPlanRequest) -> dict[str, Any]:
        if not request.title.strip():
            raise ValueError("title é obrigatório.")

        branch_code = validate_branch_code(request.branch_code, required=True)
        nonconformity_scope = validate_nonconformity_scope(request.nonconformity_scope)
        recurrence_key = build_recurrence_key(
            branch_code=branch_code,
            product_code=request.product_code,
            failure_mode=request.failure_mode,
            explicit=request.recurrence_key,
        )

        plan = self._repository.create_plan(
            {
                "title": request.title.strip(),
                "created_by_user_id": request.created_by_user_id,
                "customer_name": request.customer_name,
                "customer_contact": request.customer_contact,
                "nonconformity_scope": nonconformity_scope,
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
        if self._intelligence_sync and plan.get("id"):
            self._intelligence_sync.execute(str(plan["id"]))
        return plan


@dataclass(frozen=True)
class UpdateQualityActionPlanRequest:
    title: str | None = None
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
    severity: str | None = None
    owner_user_id: str | None = None
    branch_code: str | None = None
    nonconformity_scope: str | None = None
    department: str | None = None
    problem_category: str | None = None
    symptom_tags: list[str] | None = None
    root_cause_category: str | None = None
    failure_mode: str | None = None
    recurrence_key: str | None = None
    customer_template: str | None = None
    client_nc_registry: str | None = None


class UpdateQualityActionPlanUseCase:
    def __init__(self, repository: QualityActionPlanRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        request: UpdateQualityActionPlanRequest,
        *,
        updated_by: str,
    ) -> dict[str, Any] | None:
        fields = {
            key: value
            for key, value in request.__dict__.items()
            if value is not None
        }
        if request.branch_code is not None:
            fields["branch_code"] = validate_branch_code(request.branch_code, required=True)
        if request.nonconformity_scope is not None:
            fields["nonconformity_scope"] = validate_nonconformity_scope(
                request.nonconformity_scope
            )
        if request.customer_template is not None and request.customer_template not in {
            "generic",
            "rnc_8d",
        }:
            raise ValueError("customer_template inválido.")
        fields["updated_by_user_id"] = updated_by
        return self._repository.update_plan(plan_id, fields)


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
