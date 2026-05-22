from datetime import datetime

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.domain.ports.supplies.inventory_turnover_query_repository_port import (
    InventoryTurnoverQueryRepositoryPort,
)


class InventoryTurnoverQueryRepository(
    BaseRepository,
    InventoryTurnoverQueryRepositoryPort,
):
    KARDEX_DEFAULT_CFOPS = ("5101", "5124", "6101", "6124")

    def _build_cpv_filters(self, request: GetInventoryTurnoverRequest):
        qb = QueryBuilder()
        qb.raw("D2.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("D2.D2_FILIAL", request.branch)

        qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        qb.in_list("D2.D2_CF", self.KARDEX_DEFAULT_CFOPS)

        return qb.build()

    def get_cpv_context(self, request: GetInventoryTurnoverRequest) -> dict:
        where_clause, params = self._build_cpv_filters(request)

        sql = f"""
            SELECT
                ? AS branch,
                ISNULL(MIN(D2.D2_EMISSAO), '') AS start_date,
                ISNULL(MAX(D2.D2_EMISSAO), '') AS end_date,
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity
            FROM SD2010 D2
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