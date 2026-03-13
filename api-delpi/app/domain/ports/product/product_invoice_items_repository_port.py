# app/domain/ports/product_invoice_items_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional

from app.application.models.page import Page
from app.domain.entities.product.inbound_invoice_item import InboundInvoiceItem
from app.domain.entities.product.outbound_invoice_item import OutboundInvoiceItem


class ProductInvoiceItemsRepositoryPort(ABC):

    @abstractmethod
    def list_inbound_invoice_items(
        self,
        code: str,
        page: int,
        page_size: int,
        issue_date_start: Optional[str],
        issue_date_end: Optional[str],
        supplier: Optional[str],
        branch: Optional[str]
    ) -> Page[InboundInvoiceItem]:
        pass

    @abstractmethod
    def list_outbound_invoice_items(
        self,
        code: str,
        page: int,
        page_size: int,
        issue_date_start: Optional[str],
        issue_date_end: Optional[str],
        customer: Optional[str],
        branch: Optional[str]
    ) -> Page[OutboundInvoiceItem]:
        pass