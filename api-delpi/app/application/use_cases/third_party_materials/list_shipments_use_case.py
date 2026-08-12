from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    build_pagination,
)
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    group_shipment_rows,
)


class ListThirdPartyMaterialsShipmentsUseCase:
    def __init__(self, repository: ThirdPartyMaterialsQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        total = self._repository.count_shipments(request)
        recnos = self._repository.list_shipment_recnos(request) if total else []
        rows = (
            self._repository.list_rows_by_recnos(recnos=recnos, request=request)
            if recnos
            else []
        )
        shipments = group_shipment_rows(rows)
        order = {recno: index for index, recno in enumerate(recnos)}
        shipments.sort(key=lambda item: order.get(item["shipment_recno"], 10_000))
        return {
            "items": shipments,
            **build_pagination(
                page=request.page,
                page_size=request.page_size,
                total_items=total,
            ),
        }
