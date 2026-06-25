from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    ReopenQualityActionPlanUseCase,
    UpdateQualityActionPlanStatusUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_reopen_plan_writes_history_and_audit_log():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {"id": "plan-1", "status": "completed"},
            {"id": "plan-1", "status": "in_progress"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    result = repo.reopen_plan(
        "plan-1",
        target_status="in_progress",
        reason="Cliente solicitou revisão da contenção.",
        updated_by="coord-01",
    )

    assert result is not None
    repo.append_history.assert_called_once()
    assert repo.append_history.call_args.kwargs["event_type"] == "plan_reopened"
    repo.append_audit_log.assert_called_once()
    assert repo.append_audit_log.call_args.kwargs["event_type"] == "plan_reopened"
    repo.commit.assert_called_once()


def test_reopen_plan_rejects_non_terminal_status():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.get_plan_by_id = MagicMock(return_value={"id": "plan-1", "status": "in_progress"})

    try:
        repo.reopen_plan(
            "plan-1",
            target_status="triage",
            reason="Motivo válido aqui.",
            updated_by="user-1",
        )
        raised = False
    except ValueError as exc:
        raised = True
        assert "concluídos ou cancelados" in str(exc)

    assert raised


def test_update_plan_status_emits_plan_closed_audit_for_completed():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {"id": "plan-1", "status": "waiting_validation"},
            {"id": "plan-1", "status": "completed"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    repo.update_plan_status(
        "plan-1",
        status="completed",
        updated_by="user-1",
        comment="Eficácia confirmada.",
    )

    repo.append_history.assert_called_once()
    assert repo.append_history.call_args.kwargs["event_type"] == "plan_closed"
    repo.append_audit_log.assert_called_once_with(
        entity_type="quality_action_plan",
        entity_id="plan-1",
        event_type="plan_closed",
        actor_user_id="user-1",
        payload={
            "previous_status": "waiting_validation",
            "status": "completed",
            "comment": "Eficácia confirmada.",
        },
        auto_commit=False,
    )


def test_update_status_use_case_blocks_terminal_without_reopen_flow():
    repo = MagicMock()
    repo.get_plan_by_id.return_value = {"id": "plan-1", "status": "completed"}
    use_case = UpdateQualityActionPlanStatusUseCase(repo)

    try:
        use_case.execute("plan-1", status="in_progress", updated_by="user-1")
        raised = False
    except ValueError as exc:
        raised = True
        assert "reabertura" in str(exc)

    assert raised
    repo.update_plan_status.assert_not_called()


def test_reopen_use_case_requires_reason_min_length():
    repo = MagicMock()
    use_case = ReopenQualityActionPlanUseCase(repo)

    try:
        use_case.execute("plan-1", reason="abc", updated_by="user-1")
        raised = False
    except ValueError as exc:
        raised = True
        assert "motivo" in str(exc).lower()

    assert raised
    repo.reopen_plan.assert_not_called()


def test_reopen_use_case_defaults_target_for_cancelled():
    repo = MagicMock()
    repo.get_plan_by_id.return_value = {"id": "plan-1", "status": "cancelled"}
    repo.reopen_plan.return_value = {"id": "plan-1", "status": "triage"}
    use_case = ReopenQualityActionPlanUseCase(repo)

    use_case.execute(
        "plan-1",
        reason="Reavaliação após nova evidência do cliente.",
        updated_by="user-1",
    )

    repo.reopen_plan.assert_called_once_with(
        "plan-1",
        target_status="triage",
        reason="Reavaliação após nova evidência do cliente.",
        updated_by="user-1",
    )


def test_stalled_alert_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"stalled_plans": 2})
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "id": "plan-1",
                "code": "PAC-2026-0001",
                "title": "Oxidação",
                "branch_code": "01",
                "status": "in_progress",
                "updated_at": None,
                "days_without_update": 9,
            }
        ]
    )

    alert = repo._fetch_stalled_alert(branch_code="01")

    assert alert["stalled_plans"] == 2
    assert alert["top_plans"][0]["code"] == "PAC-2026-0001"
    assert repo.fetch_one.call_args[0][1] == (5, "01")
    assert repo.fetch_all.call_args[0][1] == (5, "01", 8)


def test_effectiveness_pending_alert_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"pending_plans": 3})
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "id": "plan-2",
                "code": "PAC-2026-0002",
                "title": "Retrabalho",
                "branch_code": "02",
                "severity": "high",
                "effectiveness_proposed_status": "effective",
                "effectiveness_submitted_at": None,
                "effectiveness_submitted_by": "user-a",
            }
        ]
    )

    alert = repo._fetch_effectiveness_pending_alert(branch_code="02")

    assert alert["pending_plans"] == 3
    assert alert["top_plans"][0]["effectiveness_proposed_status"] == "effective"
    assert repo.fetch_one.call_args[0][1] == ("02",)
    assert repo.fetch_all.call_args[0][1] == ("02", 8)
