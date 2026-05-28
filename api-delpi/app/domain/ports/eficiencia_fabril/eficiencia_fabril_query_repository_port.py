from abc import ABC, abstractmethod

from app.application.dto.eficiencia_fabril.get_eficiencia_fabril_dashboard_request import (
    GetEficienciaFabrilDashboardRequest,
)
from app.application.dto.eficiencia_fabril.eficiencia_fabril_dashboard_response import (
    EficienciaFabrilDashboardResponse,
)


class EficienciaFabrilQueryRepositoryPort(ABC):

    @abstractmethod
    def get_dashboard(
        self,
        request: GetEficienciaFabrilDashboardRequest,
    ) -> EficienciaFabrilDashboardResponse:
        raise NotImplementedError
