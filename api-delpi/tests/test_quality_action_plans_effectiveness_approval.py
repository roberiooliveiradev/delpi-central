from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    ApproveEffectivenessReviewUseCase,
    EffectivenessReviewRequest,
    RejectEffectivenessReviewUseCase,
    SubmitEffectivenessReviewUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_submit_effectiveness_review_writes_history_and_audit_log():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {"id": "plan-1", "effectiveness_approval_status": None},
            {"id": "plan-1", "effectiveness_approval_status": "pending_review"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    result = repo.submit_effectiveness_review(
        "plan-1",
        {"effectiveness_status": "effective", "notes": "Evidência anexada."},
        updated_by="analyst-01",
        updated_by_name="Ana Analista",
    )

    assert result is not None
    execute_args = repo.execute.call_args[0][1]
    assert execute_args[3] == "Ana Analista"
    repo.append_history.assert_called_once()
    assert repo.append_history.call_args.kwargs["event_type"] == "effectiveness_submitted"
    repo.append_audit_log.assert_called_once()
    assert repo.append_audit_log.call_args.kwargs["event_type"] == "effectiveness_submitted"


def test_submit_effectiveness_review_blocks_when_pending():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)
    repo.get_plan_by_id = MagicMock(
        return_value={"id": "plan-1", "effectiveness_approval_status": "pending_review"}
    )

    try:
        repo.submit_effectiveness_review(
            "plan-1",
            {"effectiveness_status": "effective"},
            updated_by="analyst-01",
        )
        raised = False
    except ValueError as exc:
        raised = True
        assert "aguardando aprovação" in str(exc)

    assert raised


def test_approve_effectiveness_review_applies_proposed_status():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {
                "id": "plan-1",
                "effectiveness_approval_status": "pending_review",
                "effectiveness_proposed_status": "partially_effective",
                "effectiveness_notes": "Parcial.",
                "effectiveness_submitted_by": "analyst-01",
            },
            {"id": "plan-1", "effectiveness_status": "partially_effective"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    result = repo.approve_effectiveness_review("plan-1", updated_by="coord-01")

    assert result is not None
    repo.append_history.assert_called_once()
    assert repo.append_history.call_args.kwargs["event_type"] == "effectiveness_reviewed"
    repo.append_audit_log.assert_called_once()
    assert repo.append_audit_log.call_args.kwargs["event_type"] == "effectiveness_approved"


def test_reject_effectiveness_review_emits_rejection_event():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {
                "id": "plan-1",
                "effectiveness_approval_status": "pending_review",
                "effectiveness_proposed_status": "effective",
                "effectiveness_submitted_by": "analyst-01",
            },
            {"id": "plan-1", "effectiveness_approval_status": "rejected"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    repo.reject_effectiveness_review(
        "plan-1",
        reason="Evidência insuficiente para concluir eficácia.",
        updated_by="coord-01",
    )

    repo.append_history.assert_called_once()
    assert repo.append_history.call_args.kwargs["event_type"] == "effectiveness_approval_rejected"


def test_submit_use_case_rejects_non_submittable_status():
    repo = MagicMock()
    use_case = SubmitEffectivenessReviewUseCase(repo)

    try:
        use_case.execute(
            "plan-1",
            EffectivenessReviewRequest(effectiveness_status="pending"),
            updated_by="user-1",
        )
        raised = False
    except ValueError as exc:
        raised = True
        assert "submissão" in str(exc).lower()

    assert raised
    repo.submit_effectiveness_review.assert_not_called()


def test_reject_use_case_requires_reason_min_length():
    repo = MagicMock()
    use_case = RejectEffectivenessReviewUseCase(repo)

    try:
        use_case.execute("plan-1", reason="abc", updated_by="coord-01")
        raised = False
    except ValueError as exc:
        raised = True
        assert "motivo" in str(exc).lower()

    assert raised
    repo.reject_effectiveness_review.assert_not_called()


def test_approve_use_case_triggers_intelligence_sync():
    repo = MagicMock()
    repo.approve_effectiveness_review.return_value = {"id": "plan-1"}
    sync = MagicMock()
    use_case = ApproveEffectivenessReviewUseCase(repo, intelligence_sync=sync)

    use_case.execute("plan-1", updated_by="coord-01")

    sync.execute.assert_called_once_with("plan-1")


def test_submit_use_case_allows_incomplete_actions():
    repo = MagicMock()
    repo.submit_effectiveness_review.return_value = {"id": "plan-1"}
    use_case = SubmitEffectivenessReviewUseCase(repo)

    result = use_case.execute(
        "plan-1",
        EffectivenessReviewRequest(effectiveness_status="effective"),
        updated_by="user-1",
    )

    assert result == {"id": "plan-1"}
    repo.submit_effectiveness_review.assert_called_once()


def test_approve_use_case_allows_incomplete_actions():
    repo = MagicMock()
    repo.approve_effectiveness_review.return_value = {"id": "plan-1"}
    use_case = ApproveEffectivenessReviewUseCase(repo)

    result = use_case.execute("plan-1", updated_by="coord-01")

    assert result == {"id": "plan-1"}
    repo.approve_effectiveness_review.assert_called_once()
