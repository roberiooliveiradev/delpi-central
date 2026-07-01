"""Testes — retenção e fluxo record/restore de revisões PAC."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.services.quality_action_plans.pac_plan_revision_snapshot_service import (
    PAC_PLAN_REVISION_RETENTION_LIMIT,
    REVISION_SCOPE_IDENTIFICATION,
    REVISION_SCOPE_RESTORE,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


@pytest.fixture
def repo() -> PostgresQualityActionPlanRepository:
    instance = PostgresQualityActionPlanRepository()
    plan_id = "11111111-1111-1111-1111-111111111111"
    instance._coerce_plan_id = MagicMock(return_value=plan_id)
    return instance


def test_prune_old_plan_revisions_skips_when_under_limit(repo) -> None:
    repo.fetch_one = MagicMock(return_value=None)
    repo.execute = MagicMock()

    repo._prune_old_plan_revisions("plan-1")

    repo.execute.assert_not_called()


def test_prune_old_plan_revisions_deletes_cutoff_and_below(repo) -> None:
    repo.fetch_one = MagicMock(return_value={"cutoff": 3})
    repo.execute = MagicMock()
    plan_id = "11111111-1111-1111-1111-111111111111"

    repo._prune_old_plan_revisions(plan_id, keep=50)

    repo.execute.assert_called_once()
    sql, params = repo.execute.call_args[0]
    assert "DELETE FROM quality.quality_action_plan_revisions" in sql
    assert params == (plan_id, 3)


def test_record_plan_revision_increments_and_prunes(repo) -> None:
    detail = {
        "plan": {"id": "11111111-1111-1111-1111-111111111111", "title": "NC"},
        "actions": [],
        "evidences": [],
        "team_members": [],
    }
    repo.get_plan_detail = MagicMock(return_value=detail)
    repo.fetch_one = MagicMock(
        side_effect=[
            {"next_revision": 2},
            {"cutoff": 1},
        ]
    )
    repo.execute = MagicMock()
    repo._prune_old_plan_revisions = MagicMock()

    revision = repo.record_plan_revision(
        "plan-1",
        change_scope=REVISION_SCOPE_IDENTIFICATION,
        created_by="user-1",
        change_summary="Título alterado.",
        auto_commit=False,
    )

    assert revision == 2
    assert repo.execute.call_count == 2
    insert_sql = repo.execute.call_args_list[0][0][0]
    update_sql = repo.execute.call_args_list[1][0][0]
    assert "INSERT INTO quality.quality_action_plan_revisions" in insert_sql
    assert "SET current_revision_number" in update_sql
    repo._prune_old_plan_revisions.assert_called_once_with(
        "11111111-1111-1111-1111-111111111111",
        auto_commit=False,
    )


def test_restore_plan_revision_applies_snapshot_and_records_restore(repo) -> None:
    plan_id = "11111111-1111-1111-1111-111111111111"
    snapshot = {
        "schema_version": 1,
        "plan": {"title": "Estado antigo", "status": "in_progress"},
        "actions": [],
        "team_members": [],
        "evidences": [],
    }
    restored_detail = {"plan": {"id": plan_id, "title": "Estado antigo"}}

    repo.get_plan_by_id = MagicMock(return_value={"id": plan_id})
    repo.get_plan_revision = MagicMock(
        return_value={"revision_number": 2, "snapshot": snapshot},
    )
    repo.apply_plan_snapshot = MagicMock()
    repo.record_plan_revision = MagicMock(return_value=3)
    repo.append_history = MagicMock()
    repo.commit = MagicMock()
    repo.get_plan_detail = MagicMock(return_value=restored_detail)

    result = repo.restore_plan_revision(
        plan_id,
        2,
        updated_by="user-1",
        updated_by_name="Ana",
    )

    assert result == restored_detail
    repo.apply_plan_snapshot.assert_called_once_with(
        plan_id,
        snapshot,
        auto_commit=False,
    )
    repo.record_plan_revision.assert_called_once()
    kwargs = repo.record_plan_revision.call_args.kwargs
    assert kwargs["change_scope"] == REVISION_SCOPE_RESTORE
    assert kwargs["restored_from_revision"] == 2
    repo.append_history.assert_called_once()
    repo.commit.assert_called_once()


def test_retention_limit_is_fifty() -> None:
    assert PAC_PLAN_REVISION_RETENTION_LIMIT == 50
