from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    as_quantity,
)


class GetThirdPartyMaterialsSummaryUseCase:
    def __init__(self, repository: ThirdPartyMaterialsQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        row = self._repository.get_summary(request)
        return {
            "total_shipments": int(row.get("total_shipments") or 0),
            "open_shipments": int(row.get("open_shipments") or 0),
            "partial_shipments": int(row.get("partial_shipments") or 0),
            "no_return_shipments": int(row.get("no_return_shipments") or 0),
            "pending_balance": as_quantity(row.get("pending_balance")),
        }
