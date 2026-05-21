from abc import ABC, abstractmethod

from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd


class SalesOrderOtdRepositoryPort(ABC):
    @abstractmethod
    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        raise NotImplementedError
