from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_coerce_plan_id_by_code() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"id": "uuid-1"})

    resolved = repo._coerce_plan_id("PAC-2026-0029")

    assert resolved == "uuid-1"
    sql, params = repo.fetch_one.call_args[0]
    assert "code = %s" in sql
    assert params == ("PAC-2026-0029",)


def test_coerce_plan_id_by_uuid() -> None:
    plan_uuid = "f0e274de-cc4b-4b68-b9cb-881408f9374b"
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"id": plan_uuid})

    resolved = repo._coerce_plan_id(plan_uuid)

    assert resolved == plan_uuid
    sql, _params = repo.fetch_one.call_args[0]
    assert "id = %s::uuid" in sql


def test_coerce_plan_id_invalid_returns_none() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock()

    assert repo._coerce_plan_id("not-a-plan") is None
    repo.fetch_one.assert_not_called()


def test_get_plan_by_id_resolves_code() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._coerce_plan_id = MagicMock(return_value="uuid-1")
    repo.fetch_one = MagicMock(
        return_value={"id": "uuid-1", "code": "PAC-2026-0029", "title": "Teste"}
    )

    plan = repo.get_plan_by_id("PAC-2026-0029")

    assert plan is not None
    assert plan["code"] == "PAC-2026-0029"
    repo._coerce_plan_id.assert_called_once_with("PAC-2026-0029")


def test_list_plans_code_filter() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"total": 0})
    repo.fetch_all = MagicMock(return_value=[])

    repo.list_plans(code="pac-2026-0029")

    query, params = repo.fetch_one.call_args[0]
    assert "p.code = %s" in query
    assert "PAC-2026-0029" in params
