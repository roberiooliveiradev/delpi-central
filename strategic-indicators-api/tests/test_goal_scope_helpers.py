from __future__ import annotations

from si_app.shared.goal_scope import (
    format_goal_scope_label,
    indicator_uses_branch_unit_measurement,
    missing_goal_label_for_view,
    resolve_goal_scope_hint_for_view,
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


def test_format_goal_scope_label() -> None:
    assert format_goal_scope_label("") == "Meta consolidada"
    assert format_goal_scope_label("01") == "Meta filial 01"


def test_resolve_goal_scope_hint_consolidated_view_branch_only() -> None:
    hint = resolve_goal_scope_hint_for_view(
        view_branch="",
        consolidated_goal=None,
        branch_goals={
            "01": {"goal_label": "50%"},
            "02": {"goal_label": "50%"},
        },
    )
    assert hint is not None
    assert "apenas por filial" in hint
    assert "01" in hint


def test_resolve_goal_scope_hint_branch_view_consolidated_only() -> None:
    hint = resolve_goal_scope_hint_for_view(
        view_branch="01",
        consolidated_goal={"goal_label": "50%"},
        branch_goals={},
    )
    assert hint is not None
    assert "consolidado" in hint.lower()
