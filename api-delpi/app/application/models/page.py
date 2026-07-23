# app/application/models/page.py
from dataclasses import dataclass
from typing import Any, Generic, List, TypeVar

from app.application.services.response_date_format_service import (
    ResponseDateFormatService,
)

T = TypeVar("T")

@dataclass
class Page(Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    def to_dict(self):
        items: list[Any] = []
        for item in self.items:
            if hasattr(item, "to_dict"):
                row = item.to_dict()
            elif isinstance(item, dict):
                row = item
            else:
                row = vars(item)
            if isinstance(row, dict):
                row = ResponseDateFormatService.format_payload_dates(row)
            items.append(row)
        return {
            "items": items,
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
        }