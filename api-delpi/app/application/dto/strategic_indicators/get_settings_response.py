from dataclasses import dataclass
from typing import Any


@dataclass
class SettingsMetaResponse:
    source: str
    updated_at: str | None
    updated_by_email: str | None


@dataclass
class GetStrategicIndicatorsSettingsResponse:
    weights: dict[str, Any]
    goals: dict[str, Any]
    parameters: dict[str, Any]
    governance: dict[str, Any]
    meta: SettingsMetaResponse