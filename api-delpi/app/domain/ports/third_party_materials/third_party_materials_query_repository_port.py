from __future__ import annotations

from typing import Protocol

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)


class ThirdPartyMaterialsQueryRepositoryPort(Protocol):
    def count_shipments(self, request: ThirdPartyMaterialsQueryRequest) -> int: ...

    def list_shipment_recnos(
        self,
        request: ThirdPartyMaterialsQueryRequest,
    ) -> list[int]: ...

    def list_rows_by_recnos(
        self,
        *,
        recnos: list[int],
        request: ThirdPartyMaterialsQueryRequest,
    ) -> list[dict]: ...

    def get_rows_by_recno(
        self,
        *,
        shipment_recno: int,
        branch: str,
        ignored_products: tuple[str, ...],
    ) -> list[dict]: ...

    def get_summary(self, request: ThirdPartyMaterialsQueryRequest) -> dict: ...

    def list_export_rows(
        self,
        request: ThirdPartyMaterialsQueryRequest,
        *,
        limit: int,
    ) -> list[dict]: ...
