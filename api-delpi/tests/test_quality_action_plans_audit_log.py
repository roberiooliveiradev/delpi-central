from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_create_plan_writes_audit_log():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.next_plan_code = MagicMock(return_value="PAC-2026-0001")
    repo.execute_returning_one = MagicMock(return_value={"id": "plan-1", "code": "PAC-2026-0001", "status": "triage"})
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()
    repo.get_plan_by_id = MagicMock(return_value={"id": "plan-1", "code": "PAC-2026-0001"})

    repo.create_plan(
        {
            "title": "Teste",
            "created_by_user_id": "user-1",
            "branch_code": "01",
            "severity": "high",
        }
    )

    repo.append_audit_log.assert_called_once()
    assert repo.append_audit_log.call_args.kwargs["event_type"] == "plan_created"


def test_list_plan_audit_log_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._plan_exists = MagicMock(return_value=True)
    repo.fetch_one = MagicMock(return_value={"total": 1})
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "id": "audit-1",
                "entity_type": "quality_action_plan",
                "entity_id": "plan-1",
                "event_type": "plan_reopened",
                "payload": {"reason": "Revisão"},
                "actor_user_id": "coord-1",
                "created_at": None,
            }
        ]
    )

    result = repo.list_plan_audit_log("plan-1")

    assert result["pagination"]["total"] == 1
    assert result["items"][0]["event_type"] == "plan_reopened"
