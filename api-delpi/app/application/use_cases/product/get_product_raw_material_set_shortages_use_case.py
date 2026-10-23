from __future__ import annotations

from typing import Any

from app.application.dto.product.product_raw_material_set_shortage_request import (
    ProductRawMaterialSetShortageRequest,
)
from app.domain.ports.product.product_raw_material_set_shortage_repository_port import (
    ProductRawMaterialSetShortageRepositoryPort,
)
from app.domain.services.product.product_raw_material_set_shortage_service import (
    build_raw_material_set_shortages,
)
from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_set_shortage_sql import (
    DEFAULT_BOM_MAX_DEPTH,
)


class GetProductRawMaterialSetShortagesUseCase:
    def __init__(self, repository: ProductRawMaterialSetShortageRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: ProductRawMaterialSetShortageRequest) -> dict[str, Any] | None:
        product = self._repository.fetch_product(request.code)
        if product is None:
            return None

        max_depth = request.max_depth or DEFAULT_BOM_MAX_DEPTH
        bom = self._repository.fetch_raw_material_bom(
            request.code, max_depth=max_depth
        )
        mother_orders = self._repository.fetch_open_mother_orders(
            code=request.code, branch=request.branch
        )
        mother_keys = [
            str(item.get("production_order") or "").strip()
            for item in mother_orders
            if str(item.get("production_order") or "").strip()
        ]
        committed_codes = (
            self._repository.fetch_committed_product_codes_for_mother_orders(
                branch=request.branch, mother_orders=mother_keys
            )
            if mother_keys
            else []
        )
        bom_by_code = {
            str(item.get("product_code") or "").strip(): item
            for item in bom
            if str(item.get("product_code") or "").strip()
        }
        codes = list(
            dict.fromkeys(
                [
                    *bom_by_code.keys(),
                    *[
                        code
                        for code in committed_codes
                        if str(code or "").strip()
                    ],
                ]
            )
        )
        stock_rows = self._repository.fetch_mp_stock(
            branch=request.branch, product_codes=codes
        )
        stock_by_code = {
            str(row.get("product_code") or "").strip(): row for row in stock_rows
        }
        materials = [
            self._merge_material(
                code=code,
                bom_row=bom_by_code.get(code),
                stock_by_code=stock_by_code,
            )
            for code in codes
        ]
        purchase_orders = self._repository.fetch_open_purchase_orders(
            branch=request.branch, product_codes=codes
        )
        commitments = self._repository.fetch_open_commitments(
            branch=request.branch, product_codes=codes
        )
        payload = build_raw_material_set_shortages(
            product=product,
            materials=materials,
            mother_orders=mother_orders,
            purchase_orders=purchase_orders,
            commitments=commitments,
        )
        payload["branch"] = request.branch
        return payload

    @staticmethod
    def _merge_material(
        *,
        code: str,
        bom_row: dict[str, Any] | None,
        stock_by_code: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        stock = stock_by_code.get(code) or {}
        base = bom_row or {
            "product_code": code,
            "product_description": "",
            "unit": "",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "bom_level": None,
            "structure_quantity": 0.0,
        }
        return {
            **base,
            "product_code": code,
            "in_bom": bom_row is not None,
            "available_stock": float(stock.get("available_stock") or 0),
            "safety_stock": float(stock.get("safety_stock") or 0),
            "unit": stock.get("unit") or base.get("unit"),
            "secondary_unit": stock.get("secondary_unit") or base.get("secondary_unit"),
            "conversion_factor": stock.get("conversion_factor")
            if stock.get("conversion_factor") is not None
            else base.get("conversion_factor"),
            "conversion_type": stock.get("conversion_type")
            or base.get("conversion_type"),
            "product_description": stock.get("product_description")
            or base.get("product_description"),
        }
