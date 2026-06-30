from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def _capture_list_query(**kwargs):
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"total": 0})
    repo.fetch_all = MagicMock(return_value=[])
    repo.list_plans(**kwargs)
    return repo.fetch_one.call_args[0][0], repo.fetch_one.call_args[0][1]


def test_list_plans_owner_filter():
    query, params = _capture_list_query(owner_user_id="user-42")
    assert "p.owner_user_id = %s" in query
    assert "user-42" in params


def test_list_plans_department_filter():
    query, params = _capture_list_query(department="Pintura")
    assert "p.department ILIKE %s" in query
    assert "%Pintura%" in params


def test_list_plans_root_cause_filter():
    query, params = _capture_list_query(root_cause_category="Método")
    assert "p.root_cause_category ILIKE %s" in query
    assert "quality_five_whys" in query
    assert params.count("%Método%") == 2


def test_list_plans_overdue_only_filter():
    query, _params = _capture_list_query(overdue_only=True)
    assert "quality_actions" in query
    assert "due_date < CURRENT_DATE" in query
    assert "p.status NOT IN ('completed', 'cancelled')" in query


def test_list_plans_code_filter():
    query, params = _capture_list_query(code="pac-2026-0029")
    assert "p.code = %s" in query
    assert "PAC-2026-0029" in params
