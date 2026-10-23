"""Canonical supplier duplicate lookup — api-delpi exact ``tax_id`` filter.

Read-only consumer of ``GET /supplies/suppliers?tax_id=`` (X4.UX-R1.S1).
Exact digit-normalized match on A2_CGC — the textual ``query`` LIKE path is
never used for duplicate checks.
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway


class DelpiSupplierDuplicateSearch:
    """``SupplierDuplicateSearchPort`` over the shared S2S gateway."""

    def __init__(self, gateway: DelpiS2SApiGateway | None = None) -> None:
        self._gateway = gateway or DelpiS2SApiGateway()

    def search_by_tax_id(
        self,
        tax_id: str,
        *,
        access_token: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        payload = self._gateway.get(
            "/supplies/suppliers",
            access_token=access_token,
            params={
                "tax_id": tax_id,
                "page_size": page_size,
                "page": page,
            },
        )
        data = unwrap_delpi_envelope(payload)
        if not isinstance(data, dict):
            raise DelpiApiGatewayError("supplier duplicate search invalid envelope")
        items = data.get("items")
        total = data.get("total")
        if not isinstance(items, list) or not isinstance(total, int):
            raise DelpiApiGatewayError("supplier duplicate search invalid payload")
        return items, total
