from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_update_plan_allows_customer_product_reference() -> None:
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo._coerce_plan_id = MagicMock(return_value="plan-1")
    repo.get_plan_by_id = MagicMock(
        side_effect=[
            {"id": "plan-1", "code": "PAC-2026-0001"},
            {"id": "plan-1", "customer_product_reference": "REF-Cliente"},
        ]
    )
    repo.execute = MagicMock()
    repo.append_history = MagicMock()
    repo.append_audit_log = MagicMock()
    repo.commit = MagicMock()

    result = repo.update_plan(
        "plan-1",
        {
            "customer_product_reference": "REF-Cliente",
            "updated_by_user_id": "user-1",
        },
    )

    assert result is not None
    update_sql = repo.execute.call_args[0][0]
    assert "customer_product_reference" in update_sql
    assert repo.execute.call_args[0][1][0] == "REF-Cliente"
