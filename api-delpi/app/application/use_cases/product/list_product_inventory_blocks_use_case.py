from __future__ import annotations

from datetime import date

from app.application.dto.product.list_product_inventory_blocks_request import (
    ListProductInventoryBlocksRequest,
)
from app.application.services.product.protheus_field_normalizer import protheus_date_to_iso
from app.domain.ports.product.product_stock_repository_port import ProductStockRepositoryPort
from app.domain.totvs.protheus_inventory_block import is_inventory_blocked, normalize_protheus_date


class ListProductInventoryBlocksUseCase:
    """Bloqueio de inventário (SB2) de vários produtos — sem inventar ausência."""

    def __init__(self, repository: ProductStockRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: ListProductInventoryBlocksRequest,
        *,
        as_of: date | None = None,
    ) -> dict:
        codes = tuple(request.product_codes)
        rows: list[dict] = []
        if codes:
            rows = self._repository.fetch_inventory_blocks(
                branch=request.branch,
                warehouse=request.warehouse,
                product_codes=codes,
            )

        day = as_of or date.today()
        items = []
        for row in rows:
            code = str(row.get("product_code") or "").strip()
            if not code:
                continue
            start_raw = normalize_protheus_date(row.get("inventory_block_start"))
            end_raw = normalize_protheus_date(row.get("inventory_block_end"))
            items.append(
                {
                    "product_code": code,
                    "branch": str(row.get("branch") or request.branch).strip(),
                    "warehouse": str(row.get("warehouse") or request.warehouse).strip(),
                    "inventory_block_start": start_raw,
                    "inventory_block_end": end_raw,
                    "inventory_block_start_iso": protheus_date_to_iso(start_raw),
                    "inventory_block_end_iso": protheus_date_to_iso(end_raw),
                    "inventory_blocked": is_inventory_blocked(
                        block_start=start_raw,
                        block_end=end_raw,
                        as_of=day,
                    ),
                }
            )

        return {
            "branch": request.branch,
            "warehouse": request.warehouse,
            "as_of": day.isoformat(),
            "product_codes": list(codes),
            "items": items,
            "summary": {
                "requested_count": len(codes),
                "returned_count": len(items),
                "blocked_count": sum(1 for item in items if item["inventory_blocked"]),
            },
        }
