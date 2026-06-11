from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductionOrdersRepository(
    BaseRepository,
    ProductionOrdersRepositoryPort,
):
    def _reference_filters(
        self,
        *,
        branch: str | None,
        work_center: str | None,
    ) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []

        if branch:
            clauses.append("AND OP.C2_FILIAL = ?")
            clauses.append("AND RE.D4_FILIAL = ?")
            clauses.append("AND OA.H8_FILIAL = ?")
            params.extend([branch, branch, branch])

        if work_center:
            clauses.append("AND OA.H8_CTRAB = ?")
            params.append(work_center)

        return "\n".join(clauses), params

    def fetch_open_orders(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]:
        extra_filters, extra_params = self._reference_filters(
            branch=branch,
            work_center=work_center,
        )
        params = [reference_date, *extra_params]

        sql = f"""
        SELECT TOP {int(limit)}
            OP.C2_FILIAL AS branch,
            OP.C2_OP AS production_order,
            OP.C2_PRODUTO AS product_code,
            P.B1_DESC AS description,
            OP.C2_QUANT AS planned_qty,
            OP.C2_QUJE AS produced_qty,
            (OP.C2_QUANT * 1000 - OP.C2_QUJE * 1000) / 1000 AS pending_qty,
            OP.C2_UM AS unit,
            OA.H8_HRINI AS start_time,
            OA.H8_DTINI AS operation_start_date,
            OA.H8_CTRAB AS work_center
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SD4010 RE WITH (NOLOCK)
            ON RE.D4_OP = OP.C2_OP
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_QUANT > OP.C2_QUJE
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          {extra_filters}
        GROUP BY
            OP.C2_FILIAL,
            OP.C2_OP,
            OP.C2_PRODUTO,
            P.B1_DESC,
            OP.C2_QUANT,
            OP.C2_QUJE,
            OP.C2_UM,
            OA.H8_HRINI,
            OA.H8_DTINI,
            OA.H8_CTRAB
        ORDER BY OA.H8_HRINI ASC, OP.C2_OP ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_finished_orders(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]:
        extra_filters, extra_params = self._reference_filters(
            branch=branch,
            work_center=work_center,
        )
        params = [reference_date, *extra_params]

        sql = f"""
        SELECT TOP {int(limit)}
            OP.C2_FILIAL AS branch,
            OP.C2_OP AS production_order,
            OP.C2_PRODUTO AS product_code,
            P.B1_DESC AS description,
            OP.C2_QUANT AS planned_qty,
            OP.C2_QUJE AS produced_qty,
            OP.C2_UM AS unit,
            OA.H8_HRINI AS start_time,
            OA.H8_HRFIM AS end_time,
            OA.H8_DTINI AS operation_start_date,
            OA.H8_DTFIM AS operation_end_date,
            OA.H8_CTRAB AS work_center
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SD4010 RE WITH (NOLOCK)
            ON RE.D4_OP = OP.C2_OP
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_QUANT = OP.C2_QUJE
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          {extra_filters}
        GROUP BY
            OP.C2_FILIAL,
            OP.C2_OP,
            OP.C2_PRODUTO,
            P.B1_DESC,
            OP.C2_QUANT,
            OP.C2_QUJE,
            OP.C2_UM,
            OA.H8_HRINI,
            OA.H8_HRFIM,
            OA.H8_DTINI,
            OA.H8_DTFIM,
            OA.H8_CTRAB
        ORDER BY OA.H8_HRINI ASC, OP.C2_OP ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_allocation_gaps(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]:
        extra_filters, extra_params = self._reference_filters(
            branch=branch,
            work_center=work_center,
        )
        params = [reference_date, *extra_params]

        sql = f"""
        SELECT TOP {int(limit)}
            RE.D4_FILIAL AS branch,
            RE.D4_OP AS production_order,
            RE.D4_PRODUTO AS component_code,
            P.B1_DESC AS description,
            RE.D4_OPERAC AS operation,
            RE.D4_QUANT AS allocated_qty,
            OA.H8_CTRAB AS work_center
        FROM SD4010 RE WITH (NOLOCK)
        INNER JOIN SC2010 OP WITH (NOLOCK)
            ON OP.C2_OP = RE.D4_OP
           AND OP.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON RE.D4_PRODUTO = P.B1_COD
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON RE.D4_OP = OA.H8_OP
           AND RE.D4_OPERAC = OA.H8_OPER
           AND OA.D_E_L_E_T_ = ''
        WHERE RE.D_E_L_E_T_ = ''
          AND OP.C2_PRIOR = '500'
          AND RE.D4_QUANT = 0
          AND OA.H8_DTINI = ?
          {extra_filters}
        ORDER BY RE.D4_OP ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_finished_without_consumption(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]:
        extra_filters, extra_params = self._reference_filters(
            branch=branch,
            work_center=work_center,
        )
        params = [reference_date, *extra_params]

        sql = f"""
        SELECT TOP {int(limit)}
            OP.C2_FILIAL AS branch,
            OP.C2_OP AS production_order,
            OP.C2_PRODUTO AS product_code,
            P.B1_DESC AS description,
            OP.C2_QUANT AS planned_qty,
            OP.C2_QUJE AS produced_qty,
            RE.D4_COD AS component_code,
            RE.D4_OPERAC AS operation,
            SUM(RE.D4_QUANT) AS allocated_qty,
            OA.H8_CTRAB AS work_center
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SD4010 RE WITH (NOLOCK)
            ON OP.C2_OP = RE.D4_OP
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON OP.C2_PRODUTO = P.B1_COD
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON RE.D4_OP = OA.H8_OP
           AND RE.D4_OPERAC = OA.H8_OPER
           AND OA.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_PRIOR = '500'
          AND OA.H8_DTINI = ?
          AND OP.C2_QUANT = OP.C2_QUJE
          {extra_filters}
        GROUP BY
            OP.C2_FILIAL,
            OP.C2_OP,
            OP.C2_PRODUTO,
            P.B1_DESC,
            OP.C2_QUANT,
            OP.C2_QUJE,
            RE.D4_COD,
            RE.D4_OPERAC,
            OA.H8_CTRAB
        HAVING SUM(RE.D4_QUANT) = 0
        ORDER BY OP.C2_OP ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))
