from dataclasses import dataclass
from typing import Optional


@dataclass
class GetSalesOrderOtdLineDetailRequest:
    branch: str
    order_number: str
    line_item: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_code_stores: Optional[list[tuple[str, str]]] = None
