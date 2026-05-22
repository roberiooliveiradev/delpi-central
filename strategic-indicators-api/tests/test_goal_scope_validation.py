import pytest

from si_app.application.services.strategic_indicators.goal_scope_validation import (
    validate_goal_scope_branch,
)
from si_app.application.services.strategic_indicators.indicator_goal_validation_error import (
    StrategicIndicatorsIndicatorGoalValidationError,
)


def test_validate_goal_scope_branch_consolidated():
    assert (
        validate_goal_scope_branch(
            goal_scope_branch=None,
            scope_type="consolidated",
        )
        == ""
    )


def test_validate_goal_scope_branch_filial_01():
    assert (
        validate_goal_scope_branch(
            goal_scope_branch="01",
            scope_type="consolidated",
        )
        == "01"
    )


def test_validate_goal_scope_branch_allows_per_unit_with_filial():
    assert (
        validate_goal_scope_branch(
            goal_scope_branch="02",
            scope_type="per_unit",
        )
        == "02"
    )
