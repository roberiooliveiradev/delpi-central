from __future__ import annotations

from app.application.dto.strategic_indicators.get_settings_response import (
    GetStrategicIndicatorsSettingsResponse,
    SettingsMetaResponse,
)
from app.domain.ports.strategic_indicators.settings_repository_port import (
    StrategicIndicatorsSettingsRepositoryPort,
)


class GetStrategicIndicatorsSettingsUseCase:
    def __init__(self, repository: StrategicIndicatorsSettingsRepositoryPort):
        self._repository = repository

    def execute(self) -> GetStrategicIndicatorsSettingsResponse:
        result = self._repository.get_settings()
        meta = result.get("meta", {})

        return GetStrategicIndicatorsSettingsResponse(
            weights=result.get("weights", {"items": []}),
            goals=result.get("goals", {"items": []}),
            parameters=result.get("parameters", {"items": []}),
            governance=result.get("governance", {"items": []}),
            meta=SettingsMetaResponse(
                source=meta.get("source", "postgres-plugins"),
                updated_at=meta.get("updated_at"),
                updated_by_email=meta.get("updated_by_email"),
            ),
        )