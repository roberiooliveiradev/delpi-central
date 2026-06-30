from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def _capture_my_queue_query(**kwargs):
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(
        side_effect=[
            {"open_actions": 2, "overdue_actions": 1},
            {"total": 2},
        ]
    )
    repo.fetch_all = MagicMock(return_value=[])
    repo.list_my_queue(**kwargs)
    count_query = repo.fetch_one.call_args_list[1][0][0]
    list_query = repo.fetch_all.call_args[0][0]
    params = repo.fetch_all.call_args[0][1]
    return count_query, list_query, params


def test_list_my_queue_filters_by_responsible_user():
    _count_query, list_query, params = _capture_my_queue_query(user_id="user-42")
    assert "quality_action_responsibles" in list_query
    assert "user-42" in params


def test_list_my_queue_overdue_only_filter():
    _count_query, list_query, _params = _capture_my_queue_query(user_id="user-42", overdue_only=True)
    assert "a.status NOT IN ('completed', 'cancelled')" in list_query
    assert "a.due_date < CURRENT_DATE" in list_query


def test_list_my_queue_sql_excludes_completed_from_overdue_flag():
    _count_query, list_query, _params = _capture_my_queue_query(user_id="user-42")
    assert "a.status NOT IN ('completed', 'cancelled')" in list_query
    assert "completed_late" in list_query
    assert "a.completed_at" in list_query
    assert "a.evidence_required" in list_query
    assert "evidence_count" in list_query


def test_list_my_queue_include_completed_filter():
    _count_query, list_query, _params = _capture_my_queue_query(
        user_id="user-42",
        include_completed=True,
    )
    assert "WHERE" in list_query
    where_clause = list_query.split("WHERE", 1)[1].split("ORDER BY", 1)[0]
    assert "a.status <> 'cancelled'" in where_clause
    assert "a.status NOT IN ('completed', 'cancelled')" not in where_clause


def test_update_action_clears_responsible_user_id():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._coerce_plan_id = MagicMock(return_value="plan-1")  # type: ignore[method-assign]
    repo.execute_returning_one = MagicMock(
        return_value={
            "id": "act-1",
            "plan_id": "plan-1",
            "action_type": "corrective",
            "description": "Teste",
            "responsible_user_id": None,
            "responsible_name": None,
            "department": None,
            "due_date": None,
            "status": "pending",
            "evidence_required": False,
            "cause_track": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }
    )
    repo.execute = MagicMock()
    repo.commit = MagicMock()
    repo.append_history = MagicMock()
    repo.get_action = MagicMock(return_value={"id": "act-1", "responsibles": []})

    repo.update_action(
        "plan-1",
        "act-1",
        {"responsible_user_id": None, "responsible_name": None},
        updated_by="user-1",
    )

    sql, params = repo.execute_returning_one.call_args[0]
    assert "responsible_user_id = %s" in sql
    assert None in params
    repo.execute.assert_called()


def test_list_my_queue_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(
        side_effect=[
            {"open_actions": 1, "overdue_actions": 1},
            {"total": 2},
        ]
    )
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "action_id": "act-1",
                "plan_id": "plan-1",
                "action_type": "corrective",
                "description": "Revisar processo",
                "responsible_user_id": "user-42",
                "responsible_name": "Ana",
                "department": "Qualidade",
                "due_date": None,
                "completed_at": None,
                "evidence_required": False,
                "evidence_count": 0,
                "action_status": "in_progress",
                "is_overdue": False,
                "completed_late": False,
                "plan_code": "PAC-001",
                "plan_title": "Oxidação",
                "plan_status": "in_progress",
                "plan_severity": "high",
                "branch_code": "01",
                "nonconformity_scope": "external",
                "customer_name": "Cliente A",
                "product_code": "90261805",
            },
            {
                "action_id": "act-2",
                "plan_id": "plan-1",
                "action_type": "corrective",
                "description": "Fechar NC",
                "responsible_user_id": "user-42",
                "responsible_name": "Ana",
                "department": "Qualidade",
                "due_date": date(2026, 6, 20),
                "completed_at": datetime(2026, 6, 24, 10, 0, tzinfo=timezone.utc),
                "evidence_required": True,
                "evidence_count": 2,
                "action_status": "completed",
                "is_overdue": False,
                "completed_late": True,
                "plan_code": "PAC-001",
                "plan_title": "Oxidação",
                "plan_status": "in_progress",
                "plan_severity": "high",
                "branch_code": "01",
                "nonconformity_scope": "external",
                "customer_name": "Cliente A",
                "product_code": "90261805",
            },
        ]
    )

    result = repo.list_my_queue(user_id="user-42", include_completed=True)

    assert result["user_id"] == "user-42"
    assert result["summary"]["open_actions"] == 1
    assert result["items"][0]["plan_code"] == "PAC-001"
    assert result["items"][0]["action_type"] == "corrective"
    assert result["items"][1]["is_overdue"] is False
    assert result["items"][1]["completed_late"] is True
    assert result["items"][1]["completed_at"] is not None
    assert result["items"][1]["evidence_required"] is True
    assert result["items"][1]["evidence_count"] == 2
