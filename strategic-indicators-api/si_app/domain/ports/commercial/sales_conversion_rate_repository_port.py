from abc import ABC, abstractmethod

from si_app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from si_app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate


class SalesConversionRateRepositoryPort(ABC):

    @abstractmethod
    def get_sales_conversion_rate(
        self,
        request: SalesConversionRateRequest
    ) -> SalesConversionRate:
        raise NotImplementedError