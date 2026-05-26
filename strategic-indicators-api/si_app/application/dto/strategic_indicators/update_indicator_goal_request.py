from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UpdateStrategicIndicatorsIndicatorGoalRequest:
    goal_id: str
    goal_label: str
    goal_value: float
    goal_periodicity: str
    indicator_id: str | None = None
    goal_year: int | None = None
    goal_scope_branch: str | None = None
    goal_mode: str = "standard"
    monthly_targets: list[dict] = field(default_factory=list)
    valid_from: str | None = None
    valid_to: str | None = None
    notes: str | None = None
    actor_user_id: str | None = None