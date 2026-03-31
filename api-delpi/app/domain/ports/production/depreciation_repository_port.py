from abc import ABC, abstractmethod

from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.depreciation_cost import DepreciationCost

class DepreciationRepositoryPort(ABC):

    @abstractmethod
    def get_depreciation_cost(
        self,
        request: ProductionRequest
    ) -> list[DepreciationCost]:
        raise NotImplementedError