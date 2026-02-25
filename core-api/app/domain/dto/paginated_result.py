# app/domain/dto/paginated_result.py

from dataclasses import dataclass
from typing import Generic, List, TypeVar

T = TypeVar("T")


@dataclass
class PaginationMeta:
    page: int
    page_size: int
    total: int
    total_pages: int


@dataclass
class PaginatedResult(Generic[T]):
    data: List[T]
    pagination: PaginationMeta