# app/application/dto/external_nc/list_external_nonconformities_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ListExternalNonconformitiesRequest:
    page: int = 1
    page_size: int = 20
    current_status: Optional[str] = None
    supplier_id: Optional[str] = None
    search: Optional[str] = None