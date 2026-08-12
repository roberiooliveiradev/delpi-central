from __future__ import annotations

from app.application.dto.third_party_materials.constantes import parse_ignored_products
from app.config import settings
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    group_shipment_rows,
)


class GetThirdPartyMaterialsShipmentUseCase:
    def __init__(self, repository: ThirdPartyMaterialsQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        shipment_recno: int,
        branch: str,
        include_test_products: bool = False,
    ) -> dict | None:
        ignored = (
            ()
            if include_test_products
            else parse_ignored_products(settings.THIRD_PARTY_MATERIALS_IGNORED_PRODUCTS)
        )
        rows = self._repository.get_rows_by_recno(
            shipment_recno=shipment_recno,
            branch=branch,
            ignored_products=ignored,
        )
        shipments = group_shipment_rows(rows)
        return shipments[0] if shipments else None
