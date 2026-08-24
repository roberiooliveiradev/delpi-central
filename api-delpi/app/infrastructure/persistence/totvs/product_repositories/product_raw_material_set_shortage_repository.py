from __future__ import annotations

from typing import Any

from app.domain.ports.product.product_raw_material_set_shortage_repository_port import (
    ProductRawMaterialSetShortageRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_set_shortage_sql import (
    DEFAULT_BOM_MAX_DEPTH,
    mp_stock_batch_sql,
    open_commitments_batch_sql,
    open_mother_orders_sql,
    open_purchase_orders_batch_sql,
    placeholders_for,
    product_header_sql,
    raw_material_bom_sql,
)


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _iso_date(value: Any) -> str | None:
    raw = _as_text(value)
    if not raw:
        return None
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class ProductRawMaterialSetShortageRepository(
    BaseRepository, ProductRawMaterialSetShortageRepositoryPort
):
    def fetch_product(self, code: str) -> dict[str, Any] | None:
        token = _as_text(code)
        if not token:
            return None
        with self as repo:
            row = repo.execute_one(product_header_sql(), (token,))
        if not row:
            return None
        return {
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "product_type": _as_text(row.get("product_type")),
            "unit": _as_text(row.get("unit")),
        }

    def fetch_raw_material_bom(
        self, code: str, *, max_depth: int
    ) -> list[dict[str, Any]]:
        token = _as_text(code)
        depth = max(int(max_depth or DEFAULT_BOM_MAX_DEPTH), 1)
        with self as repo:
            rows = repo.execute_query(raw_material_bom_sql(), (token, depth))
        return [self._map_bom_row(row) for row in rows or []]

    def fetch_open_mother_orders(
        self, *, code: str, branch: str
    ) -> list[dict[str, Any]]:
        sql, branch_params = open_mother_orders_sql(branch=branch)
        with self as repo:
            rows = repo.execute_query(sql, (_as_text(code), *branch_params))
        return [self._map_mother_order(row) for row in rows or []]

    def fetch_mp_stock(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        codes = self._codes(product_codes)
        if not codes:
            return []
        sql, params = mp_stock_batch_sql(branch=branch, product_codes=codes)
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        return [self._map_stock_row(row) for row in rows or []]

    def fetch_open_purchase_orders(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        codes = self._codes(product_codes)
        if not codes:
            return []
        sql, extra = open_purchase_orders_batch_sql(
            branch=branch, placeholders=placeholders_for(codes)
        )
        with self as repo:
            rows = repo.execute_query(sql, (*codes, *extra))
        return [self._map_purchase_order(row) for row in rows or []]

    def fetch_open_commitments(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        codes = self._codes(product_codes)
        if not codes:
            return []
        sql, extra = open_commitments_batch_sql(
            branch=branch, placeholders=placeholders_for(codes)
        )
        with self as repo:
            rows = repo.execute_query(sql, (*codes, *extra))
        return [self._map_commitment(row) for row in rows or []]

    @staticmethod
    def _codes(product_codes: list[str]) -> list[str]:
        seen: list[str] = []
        for raw in product_codes:
            code = _as_text(raw)
            if code and code not in seen:
                seen.append(code)
        return seen

    @staticmethod
    def _map_bom_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "unit": _as_text(row.get("unit")),
            "secondary_unit": _as_text(row.get("secondary_unit")),
            "conversion_factor": _as_float(row.get("conversion_factor")) or None,
            "conversion_type": _as_text(row.get("conversion_type")),
            "bom_level": _as_int(row.get("bom_level")),
            "structure_quantity": _as_float(row.get("structure_quantity")),
        }

    @staticmethod
    def _map_mother_order(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "branch": _as_text(row.get("branch")),
            "production_order": _as_text(row.get("production_order")),
            "order_number": _as_text(row.get("order_number")),
            "order_item": _as_text(row.get("order_item")),
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "planned_start_date": _iso_date(row.get("planned_start_date")),
            "due_date": _iso_date(row.get("due_date")),
            "planned_quantity": _as_float(row.get("planned_quantity")),
            "produced_quantity": _as_float(row.get("produced_quantity")),
            "open_quantity": _as_float(row.get("open_quantity")),
            "observation": _as_text(row.get("observation")),
        }

    @staticmethod
    def _map_stock_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "unit": _as_text(row.get("unit")),
            "secondary_unit": _as_text(row.get("secondary_unit")),
            "conversion_factor": _as_float(row.get("conversion_factor")) or None,
            "conversion_type": _as_text(row.get("conversion_type")),
            "available_stock": _as_float(row.get("available_stock")),
            "safety_stock": _as_float(row.get("safety_stock")),
        }

    @staticmethod
    def _map_purchase_order(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "branch": _as_text(row.get("branch")),
            "order_number": _as_text(row.get("order_number")),
            "order_item": _as_text(row.get("order_item")),
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "warehouse": _as_text(row.get("warehouse")),
            "unit": _as_text(row.get("unit")),
            "open_quantity": _as_float(row.get("open_quantity")),
            "expected_delivery_date": _iso_date(row.get("expected_delivery_date")),
            "supplier_name": _as_text(row.get("supplier_name")),
        }

    @staticmethod
    def _map_commitment(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "branch": _as_text(row.get("branch")),
            "product_code": _as_text(row.get("product_code")),
            "product_description": _as_text(row.get("product_description")),
            "warehouse": _as_text(row.get("warehouse")),
            "production_order": _as_text(row.get("production_order")),
            "commitment_date": _iso_date(row.get("commitment_date")),
            "unit": _as_text(row.get("unit")),
            "open_quantity": _as_float(row.get("open_quantity")),
            "finished_production_order": _as_text(row.get("finished_production_order")),
            "finished_product_code": _as_text(row.get("finished_product_code")),
            "finished_order_observation": _as_text(
                row.get("finished_order_observation")
            ),
        }
