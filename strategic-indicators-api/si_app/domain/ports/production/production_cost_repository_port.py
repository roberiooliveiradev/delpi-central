from abc import ABC, abstractmethod

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.production_cost import ProductionCost

class ProductionCostRepositoryPort(ABC):

    @abstractmethod
    def get_production_cost(
        self,
        request: ProductionRequest
    ) -> list[ProductionCost]:
        raise NotImplementedError