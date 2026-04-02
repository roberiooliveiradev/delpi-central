from __future__ import annotations

from app.application.dto.strategic_indicators.update_settings_request import (
    UpdateStrategicIndicatorsSettingsRequest,
)
from app.domain.ports.strategic_indicators.settings_repository_port import (
    StrategicIndicatorsSettingsRepositoryPort,
)


class StrategicIndicatorsSettingsValidationError(ValueError):
    """Erro de validação das configurações do Strategic Indicators."""


class UpdateStrategicIndicatorsSettingsUseCase:
    OFFICIAL_DEPARTMENT_IDS = {
        "financial",
        "hr",
        "commercial",
        "production",
        "quality",
        "supplies",
        "engineering",
    }

    def __init__(self, repository: StrategicIndicatorsSettingsRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: UpdateStrategicIndicatorsSettingsRequest,
    ) -> dict:
        self._validate_weights(request.weights)
        self._validate_goals(request.goals)
        self._validate_parameters(request.parameters)
        self._validate_governance(request.governance)

        return self._repository.update_settings(
            weights=request.weights,
            goals=request.goals,
            parameters=request.parameters,
            governance=request.governance,
            actor_user_id=request.actor_user_id,
            actor_email=request.actor_email,
        )

    def _validate_weights(self, weights: dict) -> None:
        items = weights.get("items", [])
        if not isinstance(items, list) or not items:
            raise StrategicIndicatorsSettingsValidationError(
                "weights.items deve ser uma lista não vazia."
            )

        department_ids = []
        total_weight = 0

        for item in items:
            department_id = item.get("department_id")
            weight_pct = item.get("weight_pct")

            if department_id not in self.OFFICIAL_DEPARTMENT_IDS:
                raise StrategicIndicatorsSettingsValidationError(
                    f"department_id inválido em weights: {department_id}"
                )

            if not isinstance(weight_pct, int):
                raise StrategicIndicatorsSettingsValidationError(
                    f"weight_pct inválido para {department_id}. Use inteiro."
                )

            department_ids.append(department_id)
            total_weight += weight_pct

        if len(set(department_ids)) != len(department_ids):
            raise StrategicIndicatorsSettingsValidationError(
                "weights.items possui department_id duplicado."
            )

        if set(department_ids) != self.OFFICIAL_DEPARTMENT_IDS:
            raise StrategicIndicatorsSettingsValidationError(
                "weights.items deve conter exatamente os 7 departamentos oficiais."
            )

        if total_weight != 100:
            raise StrategicIndicatorsSettingsValidationError(
                f"A soma dos pesos deve ser 100. Valor atual: {total_weight}."
            )

    def _validate_goals(self, goals: dict) -> None:
        items = goals.get("items", [])
        if not isinstance(items, list) or not items:
            raise StrategicIndicatorsSettingsValidationError(
                "goals.items deve ser uma lista não vazia."
            )

        for item in items:
            department_id = item.get("department_id")
            headline_goal = (item.get("headline_goal") or "").strip()
            supporting_focus = (item.get("supporting_focus") or "").strip()

            if department_id not in self.OFFICIAL_DEPARTMENT_IDS:
                raise StrategicIndicatorsSettingsValidationError(
                    f"department_id inválido em goals: {department_id}"
                )

            if not headline_goal:
                raise StrategicIndicatorsSettingsValidationError(
                    f"headline_goal obrigatório para {department_id}."
                )

            if not supporting_focus:
                raise StrategicIndicatorsSettingsValidationError(
                    f"supporting_focus obrigatório para {department_id}."
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