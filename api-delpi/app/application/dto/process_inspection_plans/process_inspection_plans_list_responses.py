from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class ProcessInspectionPlansPagination:
    page: int
    page_size: int
    total: int
    total_pages: int

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
            "is_complete": self.page >= self.total_pages if self.total_pages else True,
        }


def build_pagination(*, page: int, page_size: int, total: int) -> ProcessInspectionPlansPagination:
    total_pages = math.ceil(total / page_size) if page_size and total else 0
    return ProcessInspectionPlansPagination(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@dataclass
class ProcessInspectionPlansOrdersWithoutPlanItem:
    branch: str
    product_code: str
    product_description: str | None
    production_order: str
    observation: str | None

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "production_order": self.production_order,
            "observation": self.observation,
        }


@dataclass
class ProcessInspectionPlansOrdersWithoutPlanResponse:
    branch: str
    items: list[ProcessInspectionPlansOrdersWithoutPlanItem]
    pagination: ProcessInspectionPlansPagination

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }


@dataclass
class ProcessInspectionPlansProductsWithoutPlanItem:
    product_code: str
    product_description: str | None
    open_orders_count: int

    def to_dict(self) -> dict:
        return {
            "product_code": self.product_code,
            "product_description": self.product_description,
            "open_orders_count": self.open_orders_count,
        }


@dataclass
class ProcessInspectionPlansProductsWithoutPlanResponse:
    branch: str
    items: list[ProcessInspectionPlansProductsWithoutPlanItem]
    pagination: ProcessInspectionPlansPagination

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }


@dataclass
class ProcessInspectionPlansProductListItem:
    product_code: str
    product_description: str | None
    revision: str
    description: str | None
    inspection_type: str | None
    created_at: str | None
    start_date: str | None

    def to_dict(self) -> dict:
        return {
            "product_code": self.product_code,
            "product_description": self.product_description,
            "revision": self.revision,
            "description": self.description,
            "inspection_type": self.inspection_type,
            "created_at": self.created_at,
            "start_date": self.start_date,
        }


@dataclass
class ProcessInspectionPlansProductsResponse:
    items: list[ProcessInspectionPlansProductListItem]
    pagination: ProcessInspectionPlansPagination

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }


@dataclass
class ProcessInspectionPlansProductDetailResponse:
    product_code: str
    include_bom: bool
    items: list[dict]
    total: int

    def to_dict(self) -> dict:
        return {
            "product_code": self.product_code,
            "include_bom": self.include_bom,
            "items": list(self.items),
            "total": self.total,
        }
