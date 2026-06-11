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

    def fetch_top_items_by_work_center(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]:
        branch_filter = "AND D4.D4_FILIAL = ?" if branch else ""
        work_center_filter = "AND H8.H8_CTRAB = ?" if work_center else ""
        params: list = [date_start, date_end_exclusive]
        if branch:
            params.append(branch)
        if work_center:
            params.append(work_center)

        sql = f"""
        SELECT TOP {int(limit)}
            D4.D4_FILIAL AS branch,
            H8.H8_CTRAB AS work_center,
            D4.D4_COD AS item_code,
            SB1.B1_DESC AS description,
            SUM(D4.D4_QTDEORI) AS original_allocated_qty,
            SUM(D4.D4_QTNECES) AS required_qty,
            SUM(D4.D4_QUANT) AS allocated_balance_qty,
            COUNT(*) AS movement_count
        FROM SD4010 D4 WITH (NOLOCK)
        INNER JOIN SH8010 H8 WITH (NOLOCK)
            ON H8.H8_FILIAL = D4.D4_FILIAL
           AND H8.H8_OP = D4.D4_OP
           AND H8.H8_OPER = D4.D4_OPERAC
           AND H8.D_E_L_E_T_ = ''
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = D4.D4_COD
           AND SB1.D_E_L_E_T_ = ''
        WHERE D4.D_E_L_E_T_ = ''
          AND D4.D4_DATA >= ?
          AND D4.D4_DATA < ?
          {branch_filter}
          {work_center_filter}
        GROUP BY
            D4.D4_FILIAL,
            H8.H8_CTRAB,
            D4.D4_COD,
            SB1.B1_DESC
        ORDER BY SUM(D4.D4_QTDEORI) DESC, D4.D4_COD ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_top_items_validated(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]:
        consumption_expr = ConsumptionRealQuantityService.SQL_EXPRESSION
        branch_filter = "AND D4.D4_FILIAL = ?" if branch else ""
        params: list = [date_start, date_end_exclusive, date_start, date_end_exclusive]
        if branch:
            params.append(branch)

        sql = f"""
        SELECT TOP {int(limit)}
            D4.D4_FILIAL AS branch,
            D4.D4_COD AS item_code,
            SB1.B1_DESC AS description,
            SUM({consumption_expr}) AS real_consumption_qty
        FROM SD4010 D4 WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = D4.D4_COD
           AND SB1.D_E_L_E_T_ = ''
        WHERE D4.D_E_L_E_T_ = ''
          AND D4.D4_DATA >= ?
          AND D4.D4_DATA < ?
          {branch_filter}
          AND EXISTS (
            SELECT 1
            FROM SH6010 H6 WITH (NOLOCK)
            WHERE H6.D_E_L_E_T_ = ''
              AND H6.H6_FILIAL = D4.D4_FILIAL
              AND H6.H6_OP = D4.D4_OP
              AND H6.H6_OPERAC = D4.D4_OPERAC
              AND H6.H6_TIPO = 'P'
              AND H6.H6_DATAINI >= ?
              AND H6.H6_DATAINI < ?
          )
        GROUP BY D4.D4_FILIAL, D4.D4_COD, SB1.B1_DESC
        ORDER BY real_consumption_qty DESC, D4.D4_COD ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))
