"""OfficialProductReader — leitura oficial read-only (TOTVS via api-delpi).

Delega o Bearer humano aos contratos vigentes:
- ``GET /products/{code}?view=engineering`` — ficha SB1 autorizada;
- ``GET /products/{code}/suppliers?view=engineering`` — vínculos SA5.

Estados honestos: ``available | not_found | forbidden | unavailable |
timeout | contract_error``. Nunca inventa atributo, nunca escreve ERP.
"""

from __future__ import annotations

from typing import Any

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.delegated_auxiliary import (
    ApiDelpiDelegatedAuxiliary,
)


class ApiDelpiOfficialProductReader:
    """Adapter do port ``OfficialProductReaderPort``."""

    def __init__(self, auxiliary: ApiDelpiDelegatedAuxiliary) -> None:
        self._aux = auxiliary

    async def read_product(
        self, *, access_token: str, request_id: str, official_code: str
    ) -> dict[str, Any]:
        ctx = HomeSourceContext(
            user_id="",
            access_token=access_token,
            request_id=request_id,
        )
        detail = await self._aux.fetch_product_detail(
            ctx, code=official_code, view="engineering"
        )
        status = detail.get("status")
        if status != "available":
            return {
                "status": _map_status(status),
                "reason": detail.get("reason"),
            }
        product = (detail.get("data") or {}).get("product") or {}
        suppliers_result = await self._aux.fetch_product_suppliers(
            ctx, code=official_code, page=1, page_size=500
        )
        sup_status = suppliers_result.get("status")
        if sup_status != "available":
            return {
                "status": _map_status(sup_status),
                "reason": suppliers_result.get("reason"),
            }
        suppliers = (suppliers_result.get("data") or {}).get("items") or []
        return {
            "status": "available",
            "product": product,
            "suppliers": suppliers,
        }


def _map_status(status: str | None) -> str:
    return {
        "available": "available",
        "not_found": "not_found",
        "forbidden": "forbidden",
    }.get(status or "", "unavailable")
