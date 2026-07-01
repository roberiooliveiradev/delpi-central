from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.quality_action_plan_delete_policy import (
    assert_plan_deletable,
)


def test_assert_plan_deletable_blocks_reopened_plan_with_completion_history():
    with pytest.raises(ValueError, match="reabertura"):
        assert_plan_deletable(
            {"id": "plan-1", "status": "containment"},
            was_ever_completed=True,
        )


def test_assert_plan_deletable_allows_plan_never_completed():
    assert_plan_deletable(
        {"id": "plan-1", "status": "containment"},
        was_ever_completed=False,
    )
