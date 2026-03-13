# app/application/use_cases/products/list_product_inbound_invoice_items_use_case.py

from app.domain.ports.product.product_invoice_items_repository_port import ProductInvoiceItemsRepositoryPort
from app.application.dto.product.list_product_inbound_invoice_items_request import ListProductInboundInvoiceItemsRequest


class ListProductInboundInvoiceItemsUseCase:

    def __init__(self, repository: ProductInvoiceItemsRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductInboundInvoiceItemsRequest):

        page = self.repository.list_inbound_invoice_items(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            issue_date_start=dto.issue_date_start,
            issue_date_end=dto.issue_date_end,
            supplier=dto.supplier,
            branch=dto.branch
        )

        return page.to_dict()