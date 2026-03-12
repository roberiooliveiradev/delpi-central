# app/application/dto/list_product_guide_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductInboundInvoiceItemsRequest:

    code: str
    page: int
    page_size: int

    issue_date_start: Optional[str]
    issue_date_end: Optional[str]

    supplier: Optional[str]
    branch: Optional[str]