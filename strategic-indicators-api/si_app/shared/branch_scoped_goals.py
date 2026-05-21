from __future__ import annotations

from si_app.shared.goal_scope import format_branch_scope_label


def format_branch_scoped_goal_label(branch_goals: dict[str, dict]) -> str:
    parts: list[str] = []
    for branch_code in sorted(branch_goals.keys()):
        goal = branch_goals[branch_code]
        label = (goal.get("goal_label") or "").strip()
        scope_label = format_branch_scope_label(branch_code)
        if label:
            parts.append(f"{scope_label}: {label}")
        else:
            parts.append(scope_label)
    return " | ".join(parts)


def pick_primary_branch_goal(branch_goals: dict[str, dict]) -> dict:
    for branch_code in ("01", "02"):
        goal = branch_goals.get(branch_code)
        if goal:
            return goal
    return next(iter(branch_goals.values()))
