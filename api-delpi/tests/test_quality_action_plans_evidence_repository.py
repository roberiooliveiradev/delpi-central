from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_create_evidence_rejects_foreign_action_id():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    repo.action_belongs_to_plan = MagicMock(return_value=False)  # type: ignore[method-assign]
    repo.execute_returning_one = MagicMock(side_effect=AssertionError("should not insert"))

    result = repo.create_evidence(
        "plan-id",
        {
            "type": "image",
            "uploaded_by": "user-1",
            "action_id": "action-other-plan",
        },
    )

    assert result is None
    repo.execute_returning_one.assert_not_called()


def test_create_evidence_passes_action_id_when_valid():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    repo.action_belongs_to_plan = MagicMock(return_value=True)  # type: ignore[method-assign]
    repo.execute_returning_one = MagicMock(  # type: ignore[method-assign]
        return_value={
            "id": "ev-1",
            "plan_id": "plan-id",
            "action_id": "action-1",
            "type": "image",
            "uploaded_by": "user-1",
            "created_at": None,
        }
    )
    repo.fetch_one = MagicMock()  # type: ignore[method-assign]

    result = repo.create_evidence(
        "plan-id",
        {
            "type": "image",
            "uploaded_by": "user-1",
            "action_id": "action-1",
        },
    )

    assert result is not None
    args = repo.execute_returning_one.call_args[0][1]
    assert args[-1] == "action-1"


def test_update_evidence_rejects_foreign_action_id():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._coerce_plan_id = MagicMock(return_value="plan-id")  # type: ignore[method-assign]
    repo.get_evidence = MagicMock(return_value={"id": "ev-1", "plan_id": "plan-id"})  # type: ignore[method-assign]
    repo.action_belongs_to_plan = MagicMock(return_value=False)  # type: ignore[method-assign]
    repo.execute_returning_one = MagicMock(side_effect=AssertionError("should not update"))

    result = repo.update_evidence(
        "plan-id",
        "ev-1",
        {"action_id": "action-other-plan"},
    )

    assert result is None
    repo.execute_returning_one.assert_not_called()


def test_update_evidence_updates_allowed_fields():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._coerce_plan_id = MagicMock(return_value="plan-id")  # type: ignore[method-assign]
    repo.get_evidence = MagicMock(return_value={"id": "ev-1", "plan_id": "plan-id"})  # type: ignore[method-assign]
    repo.action_belongs_to_plan = MagicMock(return_value=True)  # type: ignore[method-assign]
    repo.execute_returning_one = MagicMock(  # type: ignore[method-assign]
        return_value={
            "id": "ev-1",
            "plan_id": "plan-id",
            "type": "pdf",
            "section": "corrective",
            "description": "Laudo atualizado",
            "action_id": "action-1",
            "created_at": None,
        }
    )

    result = repo.update_evidence(
        "plan-id",
        "ev-1",
        {
            "type": "pdf",
            "section": "corrective",
            "description": "Laudo atualizado",
            "action_id": "action-1",
        },
    )

    assert result is not None
    assert result["type"] == "pdf"
    sql = repo.execute_returning_one.call_args[0][0]
    assert "UPDATE quality.quality_problem_evidences" in sql
    params = repo.execute_returning_one.call_args[0][1]
    assert "Laudo atualizado" in params
    assert params[-2:] == ("ev-1", "plan-id")
