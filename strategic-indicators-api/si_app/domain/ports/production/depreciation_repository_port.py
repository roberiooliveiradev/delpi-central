from abc import ABC, abstractmethod

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.depreciation_cost import DepreciationCost

class DepreciationRepositoryPort(ABC):

    @abstractmethod
    def get_depreciation_cost(
        self,
        request: ProductionRequest
    ) -> list[DepreciationCost]:
        raise NotImplementedError