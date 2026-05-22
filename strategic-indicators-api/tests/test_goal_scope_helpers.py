from __future__ import annotations

from si_app.shared.goal_scope import (
    indicator_uses_branch_unit_measurement,
    missing_goal_label_for_view,
    uses_strict_branch_goal_resolution,
)


def test_strict_branch_goal_resolution() -> None:
    assert uses_strict_branch_goal_resolution("01") is True
    assert uses_strict_branch_goal_resolution(None) is False
    assert uses_strict_branch_goal_resolution("") is False


def test_indicator_uses_branch_unit_measurement() -> None:
    assert (
        indicator_uses_branch_unit_measurement(
            indicator_branch_goals={"01": {}},
            resolved_goal_scope_branch="",
            view_branch="01",
        )
        is True
    )
    assert (
        indicator_uses_branch_unit_measurement(
            indicator_branch_goals={},
            resolved_goal_scope_branch="02",
            view_branch="02",
        )
        is True
    )
    assert (
        indicator_uses_branch_unit_measurement(
            indicator_branch_goals={},
            resolved_goal_scope_branch="",
            view_branch="01",
        )
        is False
    )


def test_missing_goal_label_for_view() -> None:
    assert missing_goal_label_for_view("01") == "Sem meta para filial 01"
