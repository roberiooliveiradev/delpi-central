from dataclasses import dataclass
from typing import Any


@dataclass
class UpdateStrategicIndicatorsSettingsRequest:
    parameters: dict[str, Any]
    governance: dict[str, Any]
    actor_user_id: str | None = None
    expected_versions: dict[str, str] | None = None