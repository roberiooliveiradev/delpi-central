from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)


class OverallEquipmentEffectivenessRepositoryPort(ABC):
    @abstractmethod
    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest,
    ) -> OverallEquipmentEffectiveness:
        raise NotImplementedError

    @abstractmethod
    def list_overall_equipment_effectiveness_by_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        raise NotImplementedError