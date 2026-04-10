from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpdateStrategicIndicatorsIndicatorGoalRequest:
    goal_id: str
    goal_label: str
    goal_value: float
    goal_periodicity: str
    valid_from: str | None = None
    valid_to: str | None = None
    notes: str | None = None
    actor_user_id: str | None = None
    actor_email: str | None = None