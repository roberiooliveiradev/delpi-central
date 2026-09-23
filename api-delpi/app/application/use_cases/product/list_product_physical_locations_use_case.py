from __future__ import annotations

from app.application.dto.product.list_product_physical_locations_request import (
    ListProductPhysicalLocationsRequest,
)
from app.domain.ports.product.product_stock_repository_port import ProductStockRepositoryPort


class ListProductPhysicalLocationsUseCase:
    """Locais físicos (BZ_MPLOCAL) de vários produtos na filial — sem inventar ausência."""

    def __init__(self, repository: ProductStockRepositoryPort):
        self._repository = repository

    def execute(self, request: ListProductPhysicalLocationsRequest) -> dict:
        codes = tuple(request.product_codes)
        rows: list[dict] = []
        if codes:
            rows = self._repository.fetch_physical_locations(
                branch=request.branch,
                product_codes=codes,
            )

        items = [
            {
                "product_code": str(row.get("product_code") or "").strip(),
                "physical_location": str(row.get("physical_location") or "").strip(),
            }
            for row in rows
            if str(row.get("product_code") or "").strip()
        ]
        return {
            "branch": request.branch,
            "product_codes": list(codes),
            "items": items,
            "summary": {
                "requested_count": len(codes),
                "returned_count": len(items),
            },
        }
