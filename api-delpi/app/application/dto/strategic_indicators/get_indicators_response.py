from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IndicatorItemResponse:
    department_id: str
    department_name: str
    indicator_id: str
    indicator_name: str
    weight_pct: int
    goal_label: str
    goal_value: float
    goal_periodicity: str
    goal_mode: str = "standard"
    monthly_targets: list[dict] = field(default_factory=list)
    scope_type: str = "consolidated"
    performance_direction: str = "higher_is_better"
    value: float = 0.0
    score: float = 0.0
    gap: float = 0.0
    trend: str = "stable"
    classification: str = ""
    source: str = ""
    value_unit: str | None = None
    value_prefix: str | None = None
    value_suffix: str | None = None
    value_decimals: int = 2


@dataclass
class IndicatorFetchErrorResponse:
    department_id: str
    source: str
    message: str


@dataclass
class GetStrategicIndicatorsResponse:
    items: list[IndicatorItemResponse]
    errors: list[IndicatorFetchErrorResponse] = field(default_factory=list)

    @property
    def partial_success(self) -> bool:
        return len(self.errors) > 0