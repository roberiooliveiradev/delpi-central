from abc import ABC, abstractmethod
from typing import Optional

from app.application.dto.commercial.get_sales_order_otd_line_detail_request import (
    GetSalesOrderOtdLineDetailRequest,
)
from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.models.page import Page
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd


class SalesOrderOtdRepositoryPort(ABC):
    @abstractmethod
    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        raise NotImplementedError

    @abstractmethod
    def list_sales_order_otd_lines(
        self,
        request: GetSalesOrderOtdPanelRequest,
    ) -> Page[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_sales_order_otd_line_detail(
        self,
        request: GetSalesOrderOtdLineDetailRequest,
    ) -> Optional[dict]:
        raise NotImplementedError
