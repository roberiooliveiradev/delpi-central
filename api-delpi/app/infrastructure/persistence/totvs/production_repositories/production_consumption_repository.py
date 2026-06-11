from app.domain.services.production.consumption_real_quantity_service import (
    ConsumptionRealQuantityService,
)
from app.domain.ports.production.production_consumption_repository_port import (
    ProductionConsumptionRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionConsumptionRepository(
    BaseRepository,
    ProductionConsumptionRepositoryPort,
):
    def fetch_top_items(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        group_by: str,
    ) -> list[dict]:
        consumption_expr = ConsumptionRealQuantityService.SQL_EXPRESSION
        branch_filter = "AND D4.D4_FILIAL = ?" if branch else ""
        params: list = [date_start, date_end_exclusive]
        if branch:
            params.append(branch)

        if group_by == "branch":
            select_branch = "D4.D4_FILIAL AS branch,"
            group_by_sql = "D4.D4_FILIAL, D4.D4_COD, SB1.B1_DESC, SB1.B1_UM"
            order_by = "real_consumption_qty DESC, D4.D4_FILIAL ASC, D4.D4_COD ASC"
        else:
            select_branch = ""
            group_by_sql = "D4.D4_COD, SB1.B1_DESC, SB1.B1_UM"
            order_by = "real_consumption_qty DESC, D4.D4_COD ASC"

        sql = f"""
        SELECT TOP {int(limit)}
            {select_branch}
            D4.D4_COD AS item_code,
            SB1.B1_DESC AS description,
            SB1.B1_UM AS unit,
            SUM({consumption_expr}) AS real_consumption_qty
        FROM SD4010 D4 WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = D4.D4_COD
           AND SB1.D_E_L_E_T_ = ''
        WHERE D4.D_E_L_E_T_ = ''
          AND D4.D4_DATA >= ?
          AND D4.D4_DATA < ?
          {branch_filter}
        GROUP BY {group_by_sql}
        ORDER BY {order_by}
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))
