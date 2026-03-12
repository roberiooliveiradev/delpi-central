# app/application/dto/list_product_outbound_invoice_items_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductOutboundInvoiceItemsRequest:

    code: str
    page: int
    page_size: int

    issue_date_start: Optional[str]
    issue_date_end: Optional[str]

    customer: Optional[str]
    branch: Optional[str]