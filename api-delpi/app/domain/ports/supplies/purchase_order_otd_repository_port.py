from abc import ABC, abstractmethod

from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.application.models.page import Page
from app.domain.entities.supplies.purchase_order_otd import PurchaseOrderOtd


class PurchaseOrderOtdRepositoryPort(ABC):
    @abstractmethod
    def get_purchase_order_otd(self, request: PurchaseOrderOtdRequest) -> PurchaseOrderOtd:
        raise NotImplementedError

    @abstractmethod
    def list_purchase_order_otd_lines(
        self,
        request: GetPurchaseOrderOtdPanelRequest,
    ) -> Page[dict]:
        raise NotImplementedError
