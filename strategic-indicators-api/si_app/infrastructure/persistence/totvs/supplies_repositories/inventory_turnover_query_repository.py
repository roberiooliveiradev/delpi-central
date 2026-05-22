from datetime import datetime

from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from si_app.domain.ports.supplies.inventory_turnover_query_repository_port import (
    InventoryTurnoverQueryRepositoryPort,
)
from si_app.shared.branch_filter import effective_query_branch


class InventoryTurnoverQueryRepository(
    BaseRepository,
    InventoryTurnoverQueryRepositoryPort,
):
    DEFAULT_CFOPS = ("5101", "5102", "6101", "6102")

    def _build_stock_filters(self, request: GetInventoryTurnoverRequest):
        qb = QueryBuilder()
        qb.raw("SB2.D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("SB2.B2_FILIAL", branch)

        if request.location:
            qb.eq("SB2.B2_LOCAL", request.location)

        return qb.build()

    def _build_cpv_filters(self, request: GetInventoryTurnoverRequest):
        qb = QueryBuilder()
        qb.raw("SD3.D_E_L_E_T_ = ''")
        qb.raw("SF4.D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("SD3.D3_FILIAL", branch)

        qb.date_range("SD3.D3_EMISSAO", request.start_date, request.end_date)
        qb.in_list("SF4.F4_CF", self.DEFAULT_CFOPS)

        return qb.build()

    def get_stock_context(self, request: GetInventoryTurnoverRequest) -> dict:
        where_clause, params = self._build_stock_filters(request)

        sql = f"""
            SELECT
                ? AS branch,
                ? AS location,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SB2.B2_COD) AS total_products,
                COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
            FROM SB2010 SB2
            WHERE {where_clause}
        """

        branch_label = request.branch or "consolidated"
        location_label = request.location or "all"
        final_params = (branch_label, location_label) + params

        with self as repo:
            result = repo.execute_one(sql, final_params)

        return result or {
            "branch": branch_label,
            "location": location_label,
            "total_stock_value": 0,
            "total_stock_quantity": 0,
            "total_records": 0,
            "total_products": 0,
            "total_locations": 0,
        }

    def get_cpv_context(self, request: GetInventoryTurnoverRequest) -> dict:
        where_clause, params = self._build_cpv_filters(request)

        sql = f"""
            SELECT
                ? AS branch,
                ISNULL(MIN(SD3.D3_EMISSAO), '') AS start_date,
                ISNULL(MAX(SD3.D3_EMISSAO), '') AS end_date,
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            WHERE {where_clause}
        """

        branch_label = request.branch or "consolidated"
        final_params = (branch_label,) + params

        with self as repo:
            result = repo.execute_one(sql, final_params)

        return result or {
            "branch": branch_label,
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "cpv_total": 0,
            "total_movements": 0,
            "total_quantity": 0,
        }