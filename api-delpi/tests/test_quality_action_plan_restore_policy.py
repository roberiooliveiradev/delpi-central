from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.quality_action_plan_delete_policy import (
    assert_plan_deletable,
    assert_plan_revision_restorable,
)


def test_assert_plan_revision_restorable_blocks_reopened_plan_with_completion_history():
    plan = {"id": "plan-1", "status": "containment"}
    with pytest.raises(ValueError, match="restaurar revisão"):
        assert_plan_revision_restorable(plan, was_ever_completed=True)


def test_assert_plan_revision_restorable_blocks_approved_effectiveness():
    with pytest.raises(ValueError, match="eficácia aprovada"):
        assert_plan_revision_restorable(
            {
                "id": "plan-1",
                "status": "in_progress",
                "effectiveness_approval_status": "approved",
            },
            was_ever_completed=False,
        )


def test_assert_plan_revision_restorable_allows_active_plan():
    assert_plan_revision_restorable(
        {"id": "plan-1", "status": "containment"},
        was_ever_completed=False,
    )


def test_delete_and_restore_share_governance_for_completed_plan():
    plan = {"id": "plan-1", "status": "completed"}
    with pytest.raises(ValueError):
        assert_plan_deletable(plan, was_ever_completed=False)
    with pytest.raises(ValueError):
        assert_plan_revision_restorable(plan, was_ever_completed=False)
