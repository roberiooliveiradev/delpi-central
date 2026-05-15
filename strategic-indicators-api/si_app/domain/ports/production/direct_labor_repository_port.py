from abc import ABC, abstractmethod
from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.direct_labor_cost import DirectLaborCost

class DirectLaborRepositoryPort(ABC):

    @abstractmethod
    def get_direct_labor_cost(
        self,
        request: ProductionRequest
    ) -> list[DirectLaborCost]:
        raise NotImplementedError