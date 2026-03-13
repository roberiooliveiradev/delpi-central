# app/application/dto/list_ov_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductCustomersRequest:

    date_start: Optional[str]
    date_end: Optional[str]
    page: Optional[int] = 1
    page_size: Optional[int] 