from app.domain.ports.production.production_work_centers_repository_port import (
    ProductionWorkCentersRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionWorkCentersRepository(
    BaseRepository,
    ProductionWorkCentersRepositoryPort,
):
    def fetch_order_summary(
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

        sql = f"""
        SELECT TOP {int(limit)}
            OA.H8_CTRAB AS work_center,
            COUNT(DISTINCT CASE
                WHEN OP.C2_QUANT = OP.C2_QUJE THEN OP.C2_OP
            END) AS finished_orders_count,
            COUNT(DISTINCT CASE
                WHEN OP.C2_QUANT > OP.C2_QUJE THEN OP.C2_OP
            END) AS open_orders_count,
            COUNT(DISTINCT OP.C2_OP) AS total_orders_count
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SD4010 RE WITH (NOLOCK)
            ON OP.C2_OP = RE.D4_OP
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON RE.D4_OP = OA.H8_OP
           AND RE.D4_OPERAC = OA.H8_OPER
           AND OA.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          {branch_filters}
        GROUP BY OA.H8_CTRAB
        ORDER BY OA.H8_CTRAB ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_average_planned_time(
        self,
        *,
        reference_date: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]:
        branch_filters = ""
        params: list = [reference_date, reference_date]

        if branch:
            branch_filters = """
              AND OP.C2_FILIAL = ?
              AND RE.D4_FILIAL = ?
              AND OA.H8_FILIAL = ?
            """
            params.extend([branch, branch, branch])

        sql = f"""
        SELECT TOP {int(limit)}
            OA.H8_CTRAB AS work_center,
            CAST(
                AVG(
                    (
                        (CAST(LEFT(REPLACE(OA.H8_HRFIM, ':', ''), 2) AS INT) * 60 +
                         CAST(RIGHT(REPLACE(OA.H8_HRFIM, ':', ''), 2) AS INT))
                        -
                        (CAST(LEFT(REPLACE(OA.H8_HRINI, ':', ''), 2) AS INT) * 60 +
                         CAST(RIGHT(REPLACE(OA.H8_HRINI, ':', ''), 2) AS INT))
                    ) / 60.0
                ) AS FLOAT
            ) AS average_planned_hours
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SD4010 RE WITH (NOLOCK)
            ON OP.C2_OP = RE.D4_OP
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON RE.D4_OP = OA.H8_OP
           AND RE.D4_OPERAC = OA.H8_OPER
           AND OA.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          AND OA.H8_DTFIM = ?
          AND OA.H8_HRINI IS NOT NULL
          AND OA.H8_HRFIM IS NOT NULL
          AND OP.C2_QUANT = OP.C2_QUJE
          {branch_filters}
        GROUP BY OA.H8_CTRAB
        ORDER BY OA.H8_CTRAB ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))
