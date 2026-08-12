from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.third_party_materials.third_party_materials_sql import (
    build_count_shipments_sql,
    build_details_by_recno_sql,
    build_details_by_recnos_sql,
    build_export_sql,
    build_shipment_page_sql,
    build_summary_sql,
)


class ThirdPartyMaterialsQueryRepository(
    BaseRepository,
    ThirdPartyMaterialsQueryRepositoryPort,
):
    def count_shipments(self, request: ThirdPartyMaterialsQueryRequest) -> int:
        sql, params = build_count_shipments_sql(request)
        with self:
            row = self.execute_one(sql, params) or {}
        return int(row.get("total_items") or 0)

    def list_shipment_recnos(
        self,
        request: ThirdPartyMaterialsQueryRequest,
    ) -> list[int]:
        sql, params = build_shipment_page_sql(request)
        with self:
            rows = self.execute_query(sql, params)
        recnos: list[int] = []
        for row in rows:
            recno = row.get("RECNO_REMESSA")
            if recno is not None:
                recnos.append(int(recno))
        return recnos

    def list_rows_by_recnos(
        self,
        *,
        recnos: list[int],
        request: ThirdPartyMaterialsQueryRequest,
    ) -> list[dict]:
        del request
        sql, params = build_details_by_recnos_sql(recnos)
        if not recnos:
            return []
        with self:
            return self.execute_query(sql, params)

    def get_rows_by_recno(
        self,
        *,
        shipment_recno: int,
        branch: str,
        ignored_products: tuple[str, ...],
    ) -> list[dict]:
        sql, params = build_details_by_recno_sql(
            shipment_recno=shipment_recno,
            branch=branch,
            ignored_products=ignored_products,
        )
        with self:
            return self.execute_query(sql, params)

    def get_summary(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        sql, params = build_summary_sql(request)
        with self:
            return self.execute_one(sql, params) or {}

    def list_export_rows(
        self,
        request: ThirdPartyMaterialsQueryRequest,
        *,
        limit: int,
    ) -> list[dict]:
        sql, params = build_export_sql(request, limit=limit)
        with self:
            return self.execute_query(sql, params)
