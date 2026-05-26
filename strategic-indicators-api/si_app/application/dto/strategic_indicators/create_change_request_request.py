from dataclasses import dataclass
from typing import Any


@dataclass
class CreateStrategicIndicatorsChangeRequestRequest:
    title: str
    description: str
    target_block: str
    proposed_payload: dict[str, Any]
    actor_user_id: str | None = None