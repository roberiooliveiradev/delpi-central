from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    LINKED_PA_OR_PREFIX_FILTER_SQL,
    SC2_PA_PRODUCT_CODE_PREFIX_SQL,
)


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
           AND RE.D4_FILIAL = OP.C2_FILIAL
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.H8_FILIAL = OP.C2_FILIAL
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
           AND RE.D4_FILIAL = OP.C2_FILIAL
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.H8_FILIAL = OP.C2_FILIAL
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

        # Componente = D4_COD (não D4_PRODUTO, que é o produto pai da OP).
        # JOINs com filial evitam produto cartesiano entre filiais (timeout no consolidado).
        sql = f"""
        SELECT TOP {int(limit)}
            RE.D4_FILIAL AS branch,
            RE.D4_OP AS production_order,
            RE.D4_COD AS component_code,
            P.B1_DESC AS description,
            RE.D4_OPERAC AS operation,
            RE.D4_QUANT AS allocated_qty,
            OA.H8_CTRAB AS work_center
        FROM SD4010 RE WITH (NOLOCK)
        INNER JOIN SC2010 OP WITH (NOLOCK)
            ON OP.C2_OP = RE.D4_OP
           AND OP.C2_FILIAL = RE.D4_FILIAL
           AND OP.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = RE.D4_COD
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.H8_FILIAL = RE.D4_FILIAL
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
            ON RE.D4_OP = OP.C2_OP
           AND RE.D4_FILIAL = OP.C2_FILIAL
           AND RE.D_E_L_E_T_ = ''
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        INNER JOIN SH8010 OA WITH (NOLOCK)
            ON OA.H8_OP = RE.D4_OP
           AND OA.H8_OPER = RE.D4_OPERAC
           AND OA.H8_FILIAL = OP.C2_FILIAL
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

    def fetch_planned_vs_real_time(
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
        planned_filters, planned_params = self._planned_time_filters(
            branch=branch,
            work_center=work_center,
        )
        params = [reference_date, *extra_params, *planned_params]

        sql = f"""
        WITH TEMPO_REAL AS (
            SELECT
                OP.C2_FILIAL AS branch,
                OP.C2_OP AS production_order,
                CAST(
                    SUM(
                        DATEDIFF(
                            MINUTE,
                            CAST(OA.H8_DTINI AS DATETIME)
                                + CAST(OA.H8_HRINI AS DATETIME),
                            CAST(OA.H8_DTFIM AS DATETIME)
                                + CAST(OA.H8_HRFIM AS DATETIME)
                        )
                    ) / 60.0 AS FLOAT
                ) AS real_hours
            FROM SC2010 OP WITH (NOLOCK)
            INNER JOIN SD4010 RE WITH (NOLOCK)
                ON RE.D4_OP = OP.C2_OP
               AND RE.D4_FILIAL = OP.C2_FILIAL
               AND RE.D_E_L_E_T_ = ''
            INNER JOIN SH8010 OA WITH (NOLOCK)
                ON OA.H8_OP = RE.D4_OP
               AND OA.H8_OPER = RE.D4_OPERAC
               AND OA.H8_FILIAL = OP.C2_FILIAL
               AND OA.D_E_L_E_T_ = ''
            WHERE OP.D_E_L_E_T_ = ''
              AND OP.C2_QUANT = OP.C2_QUJE
              AND OP.C2_PRIOR = '500'
              AND OA.H8_DTINI = ?
              {extra_filters}
            GROUP BY OP.C2_FILIAL, OP.C2_OP
        ),
        TEMPO_PLANEJADO AS (
            SELECT
                OP.C2_FILIAL AS branch,
                OP.C2_OP AS production_order,
                OP.C2_PRODUTO AS product_code,
                CAST(OP.C2_QUANT AS FLOAT) AS qty_thousand,
                CAST(OP.C2_QUANT * 1000 AS FLOAT) AS qty_units,
                CAST(SUM(SG.G2_SETUP) AS FLOAT) AS setup_hours,
                CAST(SUM(SG.G2_TEMPAD * OP.C2_QUANT) AS FLOAT) AS standard_time_hours
            FROM SC2010 OP WITH (NOLOCK)
            INNER JOIN SD4010 RE WITH (NOLOCK)
                ON RE.D4_OP = OP.C2_OP
               AND RE.D4_FILIAL = OP.C2_FILIAL
               AND RE.D_E_L_E_T_ = ''
            INNER JOIN SG2010 SG WITH (NOLOCK)
                ON SG.G2_FILIAL = OP.C2_FILIAL
               AND SG.G2_PRODUTO = OP.C2_PRODUTO
               AND SG.G2_OPERAC = RE.D4_OPERAC
               AND SG.D_E_L_E_T_ = ''
            WHERE OP.D_E_L_E_T_ = ''
              AND OP.C2_QUANT = OP.C2_QUJE
              AND OP.C2_PRIOR = '500'
              {planned_filters}
            GROUP BY OP.C2_FILIAL, OP.C2_OP, OP.C2_PRODUTO, OP.C2_QUANT
        )
        SELECT TOP {int(limit)}
            P.branch,
            P.production_order,
            P.product_code,
            P.qty_thousand,
            P.qty_units,
            P.setup_hours,
            P.standard_time_hours,
            CAST(P.setup_hours + P.standard_time_hours AS FLOAT) AS planned_hours,
            R.real_hours,
            CAST(
                R.real_hours - (P.setup_hours + P.standard_time_hours) AS FLOAT
            ) AS variance_hours,
            CASE
                WHEN R.real_hours <= (P.setup_hours + P.standard_time_hours)
                    THEN 'OK'
                WHEN R.real_hours <= (P.setup_hours + P.standard_time_hours) * 1.10
                    THEN 'ATENCAO'
                ELSE 'ESTOURO'
            END AS status
        FROM TEMPO_PLANEJADO P
        INNER JOIN TEMPO_REAL R
            ON R.production_order = P.production_order
           AND R.branch = P.branch
        ORDER BY variance_hours DESC, P.production_order ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_order_by_production_order(
        self,
        *,
        production_order: str,
        branch: str | None,
        product_type: str | None = None,
    ) -> dict | None:
        branch_filter = ""
        product_type_filter = ""
        pa_product_code_filter = ""
        params: list = [production_order]

        if branch:
            branch_filter = "AND OP.C2_FILIAL = ?"
            params.append(branch)

        if product_type:
            product_type_filter = "AND RTRIM(LTRIM(P.B1_TIPO)) = ?"
            params.append(product_type)
            if product_type == "PA":
                pa_product_code_filter = f"AND {SC2_PA_PRODUCT_CODE_PREFIX_SQL}"

        sql = f"""
        SELECT TOP 1
            OP.C2_FILIAL AS branch,
            RTRIM(LTRIM(OP.C2_OP)) AS production_order,
            RTRIM(LTRIM(OP.C2_NUM)) AS order_number,
            RTRIM(LTRIM(OP.C2_ITEM)) AS order_item,
            RTRIM(LTRIM(OP.C2_SEQUEN)) AS order_sequence,
            RTRIM(LTRIM(OP.C2_PRODUTO)) AS product_code,
            RTRIM(LTRIM(P.B1_DESC)) AS product_description,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type,
            RTRIM(LTRIM(P.B1_UM)) AS unit,
            RTRIM(LTRIM(OP.C2_UM)) AS order_unit,
            RTRIM(LTRIM(P.B1_GRUPO)) AS product_group,
            RTRIM(LTRIM(OP.C2_LOCAL)) AS warehouse,
            CAST(OP.C2_QUANT AS FLOAT) AS planned_qty,
            CAST(OP.C2_QUJE AS FLOAT) AS produced_qty,
            RTRIM(LTRIM(OP.C2_PRIOR)) AS priority,
            RTRIM(LTRIM(OP.C2_STATUS)) AS order_status,
            RTRIM(LTRIM(OP.C2_OBS)) AS observation,
            CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_EMISSAO, 112), 23) AS issue_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_DATPRI, 112), 23) AS planned_start_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_DATPRF, 112), 23) AS due_date,
            CASE
                WHEN OP.C2_DATRF IS NULL OR LTRIM(RTRIM(OP.C2_DATRF)) = ''
                THEN NULL
                ELSE CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_DATRF, 112), 23)
            END AS finish_date,
            CASE
                WHEN OP.C2_DATRF IS NULL OR LTRIM(RTRIM(OP.C2_DATRF)) = ''
                THEN NULL
                ELSE DATEDIFF(
                    DAY,
                    CONVERT(DATE, OP.C2_DATPRF, 112),
                    CONVERT(DATE, OP.C2_DATRF, 112)
                )
            END AS days_diff,
            CASE
                WHEN OP.C2_DATRF IS NULL OR LTRIM(RTRIM(OP.C2_DATRF)) = ''
                THEN 'open'
                WHEN CONVERT(DATE, OP.C2_DATRF, 112) <= CONVERT(DATE, OP.C2_DATPRF, 112)
                THEN 'on_time'
                ELSE 'late'
            END AS otd_status
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(OP.C2_OP)) = ?
          {branch_filter}
          {product_type_filter}
          {pa_product_code_filter}
        ORDER BY
            CASE WHEN RTRIM(LTRIM(P.B1_TIPO)) = 'PA' AND RTRIM(LTRIM(OP.C2_SEQUEN)) = '001' THEN 0 ELSE 1 END,
            OP.C2_SEQUEN ASC
        """

        with self as repo:
            return repo.execute_one(sql, tuple(params))

    def search_orders_by_op_prefix(
        self,
        *,
        term: str,
        branches: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        # Busca leve para autocomplete (prefixo da OP): TOP N, NOLOCK, seq PA principal.
        params: list = [f"{term}%"]
        branch_filter = ""
        if branches:
            placeholders = ",".join("?" for _ in branches)
            branch_filter = f"AND OP.C2_FILIAL IN ({placeholders})"
            params.extend(branches)

        sql = f"""
        SELECT DISTINCT TOP {int(limit)}
            OP.C2_FILIAL AS branch,
            RTRIM(LTRIM(OP.C2_OP)) AS production_order,
            RTRIM(LTRIM(OP.C2_PRODUTO)) AS product_code,
            RTRIM(LTRIM(P.B1_DESC)) AS product_description,
            RTRIM(LTRIM(OP.C2_UM)) AS unit
        FROM SC2010 OP WITH (NOLOCK)
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE OP.D_E_L_E_T_ = ''
          AND RTRIM(LTRIM(OP.C2_OP)) LIKE ?
          {branch_filter}
          AND RTRIM(LTRIM(OP.C2_SEQUEN)) = '001'
        ORDER BY production_order ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    def fetch_linked_pi_orders_by_production_order(
        self,
        *,
        production_order: str,
        branch: str | None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> list[dict]:
        branch_filter_parent = ""
        branch_filter_linked = ""
        params: list = [production_order]

        if branch:
            branch_filter_parent = "AND OP.C2_FILIAL = ?"
            branch_filter_linked = "AND LINKED.C2_FILIAL = ?"
            params.extend([branch, branch])

        order_clause = self._linked_orders_order_clause(
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        sql = f"""
        WITH PARENT_OP AS (
            SELECT TOP 1
                OP.C2_FILIAL AS branch,
                OP.C2_NUM AS order_number,
                RTRIM(LTRIM(OP.C2_OP)) AS production_order
            FROM SC2010 OP WITH (NOLOCK)
            WHERE OP.D_E_L_E_T_ = ''
              AND RTRIM(LTRIM(OP.C2_OP)) = ?
              {branch_filter_parent}
        )
        SELECT
            LINKED.C2_FILIAL AS branch,
            RTRIM(LTRIM(LINKED.C2_OP)) AS production_order,
            RTRIM(LTRIM(LINKED.C2_NUM)) AS order_number,
            RTRIM(LTRIM(LINKED.C2_ITEM)) AS order_item,
            RTRIM(LTRIM(LINKED.C2_SEQUEN)) AS order_sequence,
            RTRIM(LTRIM(LINKED.C2_PRODUTO)) AS product_code,
            RTRIM(LTRIM(P.B1_DESC)) AS product_description,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type,
            RTRIM(LTRIM(P.B1_UM)) AS unit,
            RTRIM(LTRIM(P.B1_GRUPO)) AS product_group,
            RTRIM(LTRIM(LINKED.C2_LOCAL)) AS warehouse,
            CAST(LINKED.C2_QUANT AS FLOAT) AS planned_qty,
            CAST(LINKED.C2_QUJE AS FLOAT) AS produced_qty,
            RTRIM(LTRIM(LINKED.C2_PRIOR)) AS priority,
            RTRIM(LTRIM(LINKED.C2_STATUS)) AS order_status,
            RTRIM(LTRIM(LINKED.C2_OBS)) AS observation,
            CONVERT(VARCHAR(10), CONVERT(DATE, LINKED.C2_EMISSAO, 112), 23) AS issue_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, LINKED.C2_DATPRI, 112), 23) AS planned_start_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, LINKED.C2_DATPRF, 112), 23) AS due_date,
            CASE
                WHEN LINKED.C2_DATRF IS NULL OR LTRIM(RTRIM(LINKED.C2_DATRF)) = ''
                THEN NULL
                ELSE CONVERT(VARCHAR(10), CONVERT(DATE, LINKED.C2_DATRF, 112), 23)
            END AS finish_date,
            CASE
                WHEN LINKED.C2_DATRF IS NULL OR LTRIM(RTRIM(LINKED.C2_DATRF)) = ''
                THEN NULL
                ELSE DATEDIFF(
                    DAY,
                    CONVERT(DATE, LINKED.C2_DATPRF, 112),
                    CONVERT(DATE, LINKED.C2_DATRF, 112)
                )
            END AS days_diff,
            CASE
                WHEN LINKED.C2_DATRF IS NULL OR LTRIM(RTRIM(LINKED.C2_DATRF)) = ''
                THEN 'open'
                WHEN CONVERT(DATE, LINKED.C2_DATRF, 112) <= CONVERT(DATE, LINKED.C2_DATPRF, 112)
                THEN 'on_time'
                ELSE 'late'
            END AS otd_status
        FROM PARENT_OP PO
        INNER JOIN SC2010 LINKED WITH (NOLOCK)
            ON LINKED.C2_FILIAL = PO.branch
           AND LINKED.C2_NUM = PO.order_number
           AND LINKED.D_E_L_E_T_ = ''
           AND RTRIM(LTRIM(LINKED.C2_OP)) <> PO.production_order
        INNER JOIN SB1010 P WITH (NOLOCK)
            ON P.B1_COD = LINKED.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        WHERE 1 = 1
          AND {LINKED_PA_OR_PREFIX_FILTER_SQL}
          {branch_filter_linked}
        {order_clause}
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

    @staticmethod
    def _linked_orders_order_clause(
        *,
        sort_by: str | None,
        sort_dir: str,
    ) -> str:
        sort_columns = {
            "status": "otd_status",
            "branch": "branch",
            "production_order": "production_order",
            "product_code": "product_code",
            "description": "product_description",
            "due": "due_date",
            "finish": "finish_date",
            "days": "days_diff",
            "qty": "planned_qty",
        }
        sort_key = (sort_by or "").strip().lower()
        sort_column = sort_columns.get(sort_key)
        if sort_column:
            direction = "DESC" if str(sort_dir or "asc").lower() == "desc" else "ASC"
            return f"""
        ORDER BY {sort_column} {direction}, production_order ASC, product_code ASC
            """

        return """
        ORDER BY
            LINKED.C2_ITEM ASC,
            LINKED.C2_SEQUEN ASC,
            LINKED.C2_OP ASC
        """

    @staticmethod
    def _planned_time_filters(
        *,
        branch: str | None,
        work_center: str | None,
    ) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []

        if branch:
            clauses.append("AND OP.C2_FILIAL = ?")
            clauses.append("AND RE.D4_FILIAL = ?")
            clauses.append("AND SG.G2_FILIAL = ?")
            params.extend([branch, branch, branch])

        if work_center:
            clauses.append(
                """
              AND EXISTS (
                SELECT 1
                FROM SH8010 OA WITH (NOLOCK)
                WHERE OA.D_E_L_E_T_ = ''
                  AND OA.H8_OP = OP.C2_OP
                  AND OA.H8_FILIAL = OP.C2_FILIAL
                  AND OA.H8_CTRAB = ?
              )
                """
            )
            params.append(work_center)

        return "\n".join(clauses), params
