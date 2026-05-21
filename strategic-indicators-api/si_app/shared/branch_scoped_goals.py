from __future__ import annotations


def format_branch_scoped_goal_label(branch_goals: dict[str, dict]) -> str:
    parts: list[str] = []
    for branch_code in sorted(branch_goals.keys()):
        goal = branch_goals[branch_code]
        label = (goal.get("goal_label") or "").strip()
        if label:
            parts.append(f"Un. {branch_code}: {label}")
        else:
            parts.append(f"Un. {branch_code}")
    return " | ".join(parts)


def pick_primary_branch_goal(branch_goals: dict[str, dict]) -> dict:
    for branch_code in ("01", "02"):
        goal = branch_goals.get(branch_code)
        if goal:
            return goal
    return next(iter(branch_goals.values()))
