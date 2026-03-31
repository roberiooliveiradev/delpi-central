from abc import ABC, abstractmethod
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.overall_equipment_effectiveness import OverallEquipmentEffectiveness    

class OverallEquipmentEffectivenessRepositoryPort(ABC):

    @abstractmethod
    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest
    ) -> OverallEquipmentEffectiveness:
        raise NotImplementedError
