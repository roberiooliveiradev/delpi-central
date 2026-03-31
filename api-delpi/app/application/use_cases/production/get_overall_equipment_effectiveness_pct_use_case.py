from app.application.dto.production.production_request import ProductionRequest
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import OverallEquipmentEffectivenessRepositoryPort 


class GetOverallEquipmentEffectivenessPctUseCase:
    def __init__(
        self,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort
    ):
        self._overall_equipment_effectiveness_repository = overall_equipment_effectiveness_repository

    def execute(self, production_request: ProductionRequest) -> dict:
        oee = self._overall_equipment_effectiveness_repository.get_overall_equipment_effectiveness(production_request)
        oee_pct = oee.oee_pct if oee and oee.oee_pct is not None else None
        return {"overall_equipment_effectiveness_pct": oee_pct}