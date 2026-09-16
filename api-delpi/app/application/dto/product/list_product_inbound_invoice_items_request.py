# app/application/dto/list_product_inbound_invoice_items_request.py
from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ListProductInboundInvoiceItemsRequest:

    code: str
    page: int
    page_size: int

    issue_date_start: Optional[str]
    issue_date_end: Optional[str]

    supplier: Optional[str]
    branch: Optional[str]

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
