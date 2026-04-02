from dataclasses import dataclass
from typing import Any


@dataclass
class UpdateStrategicIndicatorsSettingsRequest:
    weights: dict[str, Any]
    goals: dict[str, Any]
    parameters: dict[str, Any]
    governance: dict[str, Any]
    actor_user_id: str | None = None
    actor_email: str | None = None