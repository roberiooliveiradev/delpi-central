# app/application/dto/nonconformity/list_nonconformity_request.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ListNonconformityRequest:
    type: str = "all"                  # internal | external | all
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    status: Optional[str] = None
    item_code: Optional[str] = None
    description: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None