from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.quality_action_plans.five_whys_service import (
    normalize_five_whys_payload,
)
from app.domain.services.quality_action_plans.ishikawa_causes_service import (
    normalize_ishikawa_payload,
)
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

    def get_action(
        self, plan_id: str, action_id: str
    ) -> dict[str, Any] | None: ...

    def count_evidences_for_action(self, action_id: str) -> int: ...

    def list_incomplete_plan_actions(self, plan_id: str) -> list[dict[str, Any]]: ...

    def delete_action(
        self, plan_id: str, action_id: str, *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def record_effectiveness_review(
        self, plan_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def submit_effectiveness_review(
        self, plan_id: str, fields: dict[str, Any], *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def approve_effectiveness_review(
        self, plan_id: str, *, updated_by: str
    ) -> dict[str, Any] | None: ...

    def reject_effectiveness_review(
        self, plan_id: str, *, reason: str, updated_by: str
    ) -> dict[str, Any] | None: ...

    def list_pending_effectiveness_reviews(
        self, *, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class UpsertIshikawaRequest:
    machine: list[str] | None = None
    method_process: list[str] | None = None
    material: list[str] | None = None
    manpower: list[str] | None = None
    measurement: list[str] | None = None
    environment: list[str] | None = None
    notes: str | None = None


@dataclass(frozen=True)
class UpsertFiveWhysRequest:
    occurrence_whys: list[str] | None = None
    detection_whys: list[str] | None = None
    root_cause: str | None = None
    confidence_level: str | None = None
    why_1: str | None = None
    why_2: str | None = None
    why_3: str | None = None
    why_4: str | None = None
    why_5: str | None = None
    detection_why_1: str | None = None
    detection_why_2: str | None = None
    detection_why_3: str | None = None
    detection_why_4: str | None = None
    detection_why_5: str | None = None


@dataclass(frozen=True)
class ActionResponsibleRequest:
    display_name: str
    user_id: str | None = None


@dataclass(frozen=True)
class CreateActionItemRequest:
    action_type: str
    description: str
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    responsibles: list[ActionResponsibleRequest] | None = None
    department: str | None = None
    due_date: str | None = None
    status: str = "pending"
    evidence_required: bool = False
    cause_track: str | None = None


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

SUBMITTABLE_EFFECTIVENESS = frozenset(
    {"effective", "partially_effective", "ineffective"},
)


def _with_expected_revision(
    fields: dict[str, Any],
    expected_revision_number: int | None,
) -> dict[str, Any]:
    if expected_revision_number is None:
        return fields
    return {**fields, "expected_revision_number": expected_revision_number}


class UpsertIshikawaUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        request: UpsertIshikawaRequest,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        fields = normalize_ishikawa_payload(
            {
                "machine": request.machine,
                "method_process": request.method_process,
                "material": request.material,
                "manpower": request.manpower,
                "measurement": request.measurement,
                "environment": request.environment,
                "notes": request.notes,
            }
        )
        return self._repository.upsert_ishikawa(
            plan_id,
            _with_expected_revision(fields, expected_revision_number),
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
        )


class UpsertFiveWhysUseCase:
    def __init__(
        self,
        repository: QualityActionPlanAnalysisRepository,
        intelligence_sync: Any | None = None,
    ) -> None:
        self._repository = repository
        self._intelligence_sync = intelligence_sync

    def execute(
        self,
        plan_id: str,
        request: UpsertFiveWhysRequest,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        if request.confidence_level and request.confidence_level not in {"low", "medium", "high"}:
            raise ValueError("confidence_level inválido.")
        fields = normalize_five_whys_payload(
            {
                "occurrence_whys": request.occurrence_whys,
                "detection_whys": request.detection_whys,
                "root_cause": request.root_cause,
                "confidence_level": request.confidence_level,
                "why_1": request.why_1,
                "why_2": request.why_2,
                "why_3": request.why_3,
                "why_4": request.why_4,
                "why_5": request.why_5,
                "detection_why_1": request.detection_why_1,
                "detection_why_2": request.detection_why_2,
                "detection_why_3": request.detection_why_3,
                "detection_why_4": request.detection_why_4,
                "detection_why_5": request.detection_why_5,
            }
        )
        result = self._repository.upsert_five_whys(
            plan_id,
            _with_expected_revision(fields, expected_revision_number),
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
        )
        if result and self._intelligence_sync:
            self._intelligence_sync.execute(plan_id)
        return result


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
        created_by_name: str | None = None,
        created_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        if not actions:
            raise ValueError("Informe ao menos uma ação.")
        payload: list[dict[str, Any]] = []
        for action in actions:
            if action.action_type not in self.VALID_ACTION_TYPES:
                raise ValueError(f"action_type inválido: {action.action_type}")
            if not action.description.strip():
                raise ValueError("description é obrigatória em cada ação.")
            if action.cause_track and action.cause_track not in {"occurrence", "detection"}:
                raise ValueError("cause_track inválido.")
            payload.append(
                {
                    "action_type": action.action_type,
                    "description": action.description.strip(),
                    "responsible_user_id": action.responsible_user_id,
                    "responsible_name": action.responsible_name,
                    "responsibles": (
                        [
                            {"user_id": item.user_id, "display_name": item.display_name.strip()}
                            for item in action.responsibles
                            if item.display_name.strip()
                        ]
                        if action.responsibles is not None
                        else None
                    ),
                    "department": action.department,
                    "due_date": action.due_date,
                    "status": action.status,
                    "evidence_required": action.evidence_required,
                    "cause_track": action.cause_track,
                }
            )
        return self._repository.create_actions(
            plan_id,
            payload,
            created_by=created_by,
            created_by_name=created_by_name,
            created_by_email=created_by_email,
            expected_revision_number=expected_revision_number,
        )


class RecordEffectivenessReviewUseCase:
    def __init__(
        self,
        repository: QualityActionPlanAnalysisRepository,
        intelligence_sync: Any | None = None,
    ) -> None:
        self._repository = repository
        self._intelligence_sync = intelligence_sync

    def execute(
        self,
        plan_id: str,
        request: EffectivenessReviewRequest,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        if request.effectiveness_status not in VALID_EFFECTIVENESS:
            raise ValueError("effectiveness_status inválido.")
        plan = self._repository.record_effectiveness_review(
            plan_id,
            _with_expected_revision(
                {
                    "effectiveness_status": request.effectiveness_status,
                    "notes": request.notes,
                },
                expected_revision_number,
            ),
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
        )
        if plan and self._intelligence_sync:
            self._intelligence_sync.execute(plan_id)
        return plan


class SubmitEffectivenessReviewUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        request: EffectivenessReviewRequest,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        if request.effectiveness_status not in SUBMITTABLE_EFFECTIVENESS:
            raise ValueError(
                "Para submissão, informe effective, partially_effective ou ineffective."
            )
        return self._repository.submit_effectiveness_review(
            plan_id,
            _with_expected_revision(
                {
                    "effectiveness_status": request.effectiveness_status,
                    "notes": request.notes,
                },
                expected_revision_number,
            ),
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
        )


class ApproveEffectivenessReviewUseCase:
    def __init__(
        self,
        repository: QualityActionPlanAnalysisRepository,
        intelligence_sync: Any | None = None,
    ) -> None:
        self._repository = repository
        self._intelligence_sync = intelligence_sync

    def execute(
        self,
        plan_id: str,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        plan = self._repository.approve_effectiveness_review(
            plan_id,
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
            expected_revision_number=expected_revision_number,
        )
        if plan and self._intelligence_sync:
            self._intelligence_sync.execute(plan_id)
        return plan


class RejectEffectivenessReviewUseCase:
    MIN_REASON_LENGTH = 5

    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        *,
        reason: str,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        cleaned = (reason or "").strip()
        if len(cleaned) < self.MIN_REASON_LENGTH:
            raise ValueError("Informe o motivo da rejeição com ao menos 5 caracteres.")
        return self._repository.reject_effectiveness_review(
            plan_id,
            reason=cleaned,
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
            expected_revision_number=expected_revision_number,
        )


class ListPendingEffectivenessReviewsUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(self, *, page: int = 1, page_size: int = 20):
        return self._repository.list_pending_effectiveness_reviews(
            page=page,
            page_size=page_size,
        )


class UpdatePlanActionUseCase:
    VALID_STATUSES = {"pending", "in_progress", "blocked", "completed", "cancelled", "overdue"}
    VALID_ACTION_TYPES = CreatePlanActionsUseCase.VALID_ACTION_TYPES

    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        action_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ):
        status = fields.get("status")
        if status is not None and status not in self.VALID_STATUSES:
            raise ValueError("status da ação inválido.")
        action_type = fields.get("action_type")
        if action_type is not None and action_type not in self.VALID_ACTION_TYPES:
            raise ValueError(f"action_type inválido: {action_type}")
        if fields.get("cause_track") == "":
            fields = {**fields, "cause_track": None}
        if status == "completed":
            action = self._repository.get_action(plan_id, action_id)
            if not action:
                return None
            if action.get("evidence_required") and self._repository.count_evidences_for_action(
                action_id
            ) < 1:
                raise ValueError(
                    "Não é possível concluir a ação sem evidência vinculada."
                )
        return self._repository.update_action(
            plan_id,
            action_id,
            fields,
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
        )


class DeletePlanActionUseCase:
    def __init__(self, repository: QualityActionPlanAnalysisRepository) -> None:
        self._repository = repository

    def execute(
        self,
        plan_id: str,
        action_id: str,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        expected_revision_number: int | None = None,
    ):
        return self._repository.delete_action(
            plan_id,
            action_id,
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            updated_by_email=updated_by_email,
            expected_revision_number=expected_revision_number,
        )
