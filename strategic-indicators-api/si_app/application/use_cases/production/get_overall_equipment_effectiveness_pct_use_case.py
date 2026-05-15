from __future__ import annotations

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)


class GetOverallEquipmentEffectivenessPctUseCase:
    def __init__(
        self,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
    ):
        self._overall_equipment_effectiveness_repository = (
            overall_equipment_effectiveness_repository
        )

    def execute(self, production_request: ProductionRequest) -> dict:
        if production_request.branch:
            oee = self._overall_equipment_effectiveness_repository.get_overall_equipment_effectiveness(
                production_request
            )

            oee_pct = (
                round(float(oee.oee_pct), 2)
                if oee and oee.oee_pct is not None
                else None
            )
            return {"overall_equipment_effectiveness_pct": oee_pct}

        rows = self._overall_equipment_effectiveness_repository.list_overall_equipment_effectiveness_by_branch(
            production_request
        )

        values = []
        for row in rows or []:
            value = row.get("oee_pct")
            try:
                if value is not None:
                    values.append(float(value))
            except (TypeError, ValueError):
                continue

        return {
            "overall_equipment_effectiveness_pct": (
                round(sum(values) / len(values), 2)
                if values
                else None
            )
        }