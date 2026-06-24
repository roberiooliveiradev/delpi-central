from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class QualityActionPlanAnalysisRepository(Protocol):
    def upsert_ishikawa(
        self, plan_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def upsert_five_whys(
        self, plan_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def create_actions(
        self, plan_id: str, actions: list[dict[str, Any]], *, created_by: str
    ) -> list[dict[str, Any]] | None: ...

    def update_action(
        self, plan_id: str, action_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def record_effectiveness_review(
        self, plan_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class UpsertIshikawaRequest:
    machine: str | None = None
    method_process: str | None = None
    material: str | None = None
    manpower: str | None = None
    measurement: str | None = None
    environment: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class UpsertFiveWhysRequest:
    why_1: str | None = None
    why_2: str | None = None
    why_3: str | None = None
    why_4: str | None = None
    why_5: str | None = None
    root_cause: str | None = None
    confidence_level: str | None = None


@dataclass(frozen=True)
class CreateActionItemRequest:
    action_type: str
    description: str
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    department: str | None = None
    due_date: str | None = None
    status: str = "pending"
    evidence_required: bool = False


@dataclass(frozen=True)
class EffectivenessReviewRequest:
    effectiveness_status: str
    notes: str | None = None


VALID_EFFECTIVENESS = {
    "pending",
    "effective",
    "partially_effective",
    "ineffective",
    "not_verified",
}


class UpsertIshikawaUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str, request: UpsertIshikawaRequest, *, updated_by: str):
        return self._repository.upsert_ishikawa(
            plan_id,
            {
                "machine": request.machine,
                "method_process": request.method_process,
                "material": request.material,
                "manpower": request.manpower,
                "measurement": request.measurement,
                "environment": request.environment,
                "notes": request.notes,
            },
            updated_by=updated_by,
        )


class UpsertFiveWhysUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str, request: UpsertFiveWhysRequest, *, updated_by: str):
        if request.confidence_level and request.confidence_level not in {"low", "medium", "high"}:
            raise ValueError("confidence_level inválido.")
        return self._repository.upsert_five_whys(
            plan_id,
            {
                "why_1": request.why_1,
                "why_2": request.why_2,
                "why_3": request.why_3,
                "why_4": request.why_4,
                "why_5": request.why_5,
                "root_cause": request.root_cause,
                "confidence_level": request.confidence_level,
            },
            updated_by=updated_by,
        )


class CreatePlanActionsUseCase:
    VALID_ACTION_TYPES = {
        "containment",
        "corrective",
        "preventive",
        "verification",
        "standardization",
        "training",
    }

    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        actions: list[CreateActionItemRequest],
        *,
        created_by: str,
    ):
        if not actions:
            raise ValueError("Informe ao menos uma ação.")
        payload: list[dict[str, Any]] = []
        for action in actions:
            if action.action_type not in self.VALID_ACTION_TYPES:
                raise ValueError(f"action_type inválido: {action.action_type}")
            if not action.description.strip():
                raise ValueError("description é obrigatória em cada ação.")
            payload.append(
                {
                    "action_type": action.action_type,
                    "description": action.description.strip(),
                    "responsible_user_id": action.responsible_user_id,
                    "responsible_name": action.responsible_name,
                    "department": action.department,
                    "due_date": action.due_date,
                    "status": action.status,
                    "evidence_required": action.evidence_required,
                }
            )
        return self._repository.create_actions(plan_id, payload, created_by=created_by)


class RecordEffectivenessReviewUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        request: EffectivenessReviewRequest,
        *,
        updated_by: str,
    ):
        if request.effectiveness_status not in VALID_EFFECTIVENESS:
            raise ValueError("effectiveness_status inválido.")
        return self._repository.record_effectiveness_review(
            plan_id,
            {
                "effectiveness_status": request.effectiveness_status,
                "notes": request.notes,
            },
            updated_by=updated_by,
        )


class UpdatePlanActionUseCase:
    VALID_STATUSES = {"pending", "in_progress", "blocked", "completed", "cancelled", "overdue"}

    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        action_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
    ):
        status = fields.get("status")
        if status is not None and status not in self.VALID_STATUSES:
            raise ValueError("status da ação inválido.")
        return self._repository.update_action(plan_id, action_id, fields, updated_by=updated_by)
