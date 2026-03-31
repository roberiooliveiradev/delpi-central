from abc import ABC, abstractmethod

from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.production_cost import ProductionCost

class ProductionCostRepositoryPort(ABC):

    @abstractmethod
    def get_production_cost(
        self,
        request: ProductionRequest
    ) -> list[ProductionCost]:
        raise NotImplementedError