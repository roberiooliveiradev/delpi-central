from __future__ import annotations

from app.application.dto.production.production_request import ProductionRequest
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
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

            oee_pct = to_optional_float(oee.oee_pct if oee else None)
            return {
                "overall_equipment_effectiveness_pct": (
                    round(oee_pct, 2) if oee_pct is not None else None
                )
            }

        rows = self._overall_equipment_effectiveness_repository.list_overall_equipment_effectiveness_by_branch(
            production_request
        )

        values = []
        for row in rows or []:
            parsed = to_optional_float(row.get("oee_pct"))
            if parsed is not None:
                values.append(parsed)

        return {
            "overall_equipment_effectiveness_pct": (
                round(sum(values) / len(values), 2)
                if values
                else None
            )
        }