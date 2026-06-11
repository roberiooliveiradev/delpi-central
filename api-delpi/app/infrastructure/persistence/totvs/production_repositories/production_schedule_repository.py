from app.domain.ports.production.production_schedule_repository_port import (
    ProductionScheduleRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionScheduleRepository(
    BaseRepository,
    ProductionScheduleRepositoryPort,
):
    def fetch_schedule_today(
        self,
        *,
        reference_date: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]:
        branch_filters = ""
        params: list = [reference_date]

        if branch:
            branch_filters = """
              AND OP.C2_FILIAL = ?
              AND RE.D4_FILIAL = ?
              AND OA.H8_FILIAL = ?
            """
            params.extend([branch, branch, branch])

        params_for_query = params.copy()
        sql = f"""
        SELECT TOP {int(limit)}
            OP.C2_FILIAL AS branch,
            OP.C2_OP AS production_order,
            OP.C2_PRODUTO AS product_code,
            P.B1_DESC AS description,
            OP.C2_QUANT AS planned_qty,
            OP.C2_UM AS unit,
            OP.C2_PRIOR AS priority,
            OA.H8_DTINI AS operation_start_date
        FROM SC2010 OP WITH (NOLOCK)
        LEFT JOIN SD4010 RE WITH (NOLOCK)
            ON RE.D4_OP = OP.C2_OP
           AND RE.D_E_L_E_T_ = ''
        LEFT JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.D_E_L_E_T_ = ''
        LEFT JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          {branch_filters}
          AND P.B1_TIPO = 'PA'
        GROUP BY
            OP.C2_FILIAL,
            OP.C2_OP,
            OP.C2_PRODUTO,
            P.B1_DESC,
            OP.C2_QUANT,
            OP.C2_UM,
            OP.C2_PRIOR,
            OA.H8_DTINI
        ORDER BY OP.C2_PRODUTO ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params_for_query))
