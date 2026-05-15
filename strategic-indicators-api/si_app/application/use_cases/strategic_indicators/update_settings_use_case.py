from __future__ import annotations

from si_app.application.dto.strategic_indicators.update_settings_request import (
    UpdateStrategicIndicatorsSettingsRequest,
)
from si_app.domain.ports.strategic_indicators.settings_repository_port import (
    StrategicIndicatorsSettingsRepositoryPort,
)


class StrategicIndicatorsSettingsValidationError(ValueError):
    """Erro de validação das configurações do Strategic Indicators."""


class UpdateStrategicIndicatorsSettingsUseCase:
    def __init__(self, repository: StrategicIndicatorsSettingsRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: UpdateStrategicIndicatorsSettingsRequest,
    ) -> dict:
        self._validate_parameters(request.parameters)
        self._validate_governance(request.governance)

        return self._repository.update_settings(
            parameters=request.parameters,
            governance=request.governance,
            actor_user_id=request.actor_user_id,
            actor_email=request.actor_email,
        )

    def _validate_parameters(self, parameters: dict) -> None:
        items = parameters.get("items", [])
        if not isinstance(items, list):
            raise StrategicIndicatorsSettingsValidationError(
                "parameters.items deve ser uma lista."
            )

        keys = []
        for item in items:
            key = (item.get("key") or "").strip()
            label = (item.get("label") or "").strip()
            value = (item.get("value") or "").strip()

            if not key or not label or not value:
                raise StrategicIndicatorsSettingsValidationError(
                    "Todos os parâmetros devem ter key, label e value."
                )

            keys.append(key)

        if len(set(keys)) != len(keys):
            raise StrategicIndicatorsSettingsValidationError(
                "parameters.items possui key duplicada."
            )

    def _validate_governance(self, governance: dict) -> None:
        items = governance.get("items", [])
        if not isinstance(items, list):
            raise StrategicIndicatorsSettingsValidationError(
                "governance.items deve ser uma lista."
            )