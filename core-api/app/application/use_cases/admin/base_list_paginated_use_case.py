# app/application/use_cases/admin/base_list_paginated_use_case.py

from typing import Generic, TypeVar
from app.application.unit_of_work import UnitOfWork
from app.domain.dto.paginated_result import PaginatedResult, PaginationMeta

T = TypeVar("T")


class BaseListPaginatedUseCase(Generic[T]):

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _build_result(self, items, total, page, page_size):
        total_pages = (total + page_size - 1) // page_size

        return PaginatedResult(
            data=items,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )