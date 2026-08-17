from __future__ import annotations

from app.domain.ports.process_inspection_plans.process_inspection_plans_repository_port import (
    ProcessInspectionPlansRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.process_inspection_plans import (
    process_inspection_plans_sql as sql,
)


def _as_int(value) -> int:
    if value is None or value == "":
        return 0
    return int(value)


class ProcessInspectionPlansRepository(
    BaseRepository,
    ProcessInspectionPlansRepositoryPort,
):
    def get_summary(self, branch_scope: str) -> dict:
        query, params = sql.build_summary_sql(branch_scope)
        with self as repo:
            row = repo.execute_one(query, params)
        return row or {
            "total_open_orders": 0,
            "orders_without_plan": 0,
            "products_without_plan": 0,
            "orders_with_plan": 0,
        }

    def count_orders_without_plan(self, branch_scope: str) -> int:
        query, params = sql.build_count_orders_without_plan_sql(branch_scope)
        with self as repo:
            row = repo.execute_one(query, params)
        return _as_int((row or {}).get("total"))

    def list_orders_without_plan(
        self,
        branch_scope: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]:
        offset = (page - 1) * page_size
        query, params = sql.build_list_orders_without_plan_sql(
            branch_scope,
            offset=offset,
            page_size=page_size,
        )
        with self as repo:
            return repo.execute_query(query, params)

    def count_products_without_plan(self, branch_scope: str) -> int:
        query, params = sql.build_count_products_without_plan_sql(branch_scope)
        with self as repo:
            row = repo.execute_one(query, params)
        return _as_int((row or {}).get("total"))

    def list_products_without_plan(
        self,
        branch_scope: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]:
        offset = (page - 1) * page_size
        query, params = sql.build_list_products_without_plan_sql(
            branch_scope,
            offset=offset,
            page_size=page_size,
        )
        with self as repo:
            return repo.execute_query(query, params)

    def count_products_with_plan(self) -> int:
        query, params = sql.build_count_products_with_plan_sql()
        with self as repo:
            row = repo.execute_one(query, params)
        return _as_int((row or {}).get("total"))

    def list_products_with_plan(
        self,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]:
        offset = (page - 1) * page_size
        query, params = sql.build_list_products_with_plan_sql(
            offset=offset,
            page_size=page_size,
        )
        with self as repo:
            return repo.execute_query(query, params)

    def product_has_plan(self, product_code: str) -> bool:
        query, params = sql.build_product_has_plan_sql(product_code)
        with self as repo:
            row = repo.execute_one(query, params)
        return bool(row)
