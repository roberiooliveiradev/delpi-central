from datetime import datetime, timedelta

from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from si_app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)


class StockValueQueryRepository(BaseRepository, StockValueQueryRepositoryPort):

    _HISTORICAL_STOCK_SQL = """
        WITH ultima_data_sb9 AS (
            SELECT
                B9_FILIAL AS FILIAL,
                MAX(B9_DATA) AS DATA_FECHAMENTO_BASE
            FROM SB9010
            WHERE D_E_L_E_T_ = ''
              AND B9_DATA <> ''
              AND B9_DATA < ?
              {sb9_branch_filter}
            GROUP BY B9_FILIAL
        ),
        fechamento_base AS (
            SELECT
                B9.B9_FILIAL AS FILIAL,
                U.DATA_FECHAMENTO_BASE,
                SUM(B9.B9_QINI) AS QTD_FECHAMENTO_BASE,
                SUM(B9.B9_VINI1) AS VALOR_FECHAMENTO_BASE
            FROM SB9010 B9
            INNER JOIN ultima_data_sb9 U
                ON U.FILIAL = B9.B9_FILIAL
               AND U.DATA_FECHAMENTO_BASE = B9.B9_DATA
            WHERE B9.D_E_L_E_T_ = ''
              {sb9_branch_filter_b9}
            GROUP BY
                B9.B9_FILIAL,
                U.DATA_FECHAMENTO_BASE
        ),
        mov_entre_base_e_inicio AS (
            SELECT
                D3.D3_FILIAL AS FILIAL,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_QUANT
                        ELSE -D3.D3_QUANT
                    END
                ) AS QTD_MOV_ATE_INICIO,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1
                        ELSE -D3.D3_CUSTO1
                    END
                ) AS VALOR_MOV_ATE_INICIO
            FROM SD3010 D3
            INNER JOIN ultima_data_sb9 U
                ON U.FILIAL = D3.D3_FILIAL
            WHERE D3.D_E_L_E_T_ = ''
              AND D3.D3_EMISSAO > U.DATA_FECHAMENTO_BASE
              AND D3.D3_EMISSAO < ?
              {d3_branch_filter}
            GROUP BY
                D3.D3_FILIAL
        ),
        mov_periodo AS (
            SELECT
                D3.D3_FILIAL AS FILIAL,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_QUANT
                        ELSE -D3.D3_QUANT
                    END
                ) AS QTD_MOV_LIQ_PERIODO,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1
                        ELSE -D3.D3_CUSTO1
                    END
                ) AS VALOR_MOV_LIQ_PERIODO
            FROM SD3010 D3
            WHERE D3.D_E_L_E_T_ = ''
              AND D3.D3_EMISSAO >= ?
              AND D3.D3_EMISSAO < ?
              {d3_branch_filter}
            GROUP BY
                D3.D3_FILIAL
        )
        SELECT
            COALESCE(FB.FILIAL, MI.FILIAL, MP.FILIAL) AS branch,
            FB.DATA_FECHAMENTO_BASE AS closing_base_date,
            COALESCE(FB.QTD_FECHAMENTO_BASE, 0) AS closing_base_quantity,
            COALESCE(FB.VALOR_FECHAMENTO_BASE, 0) AS closing_base_value,
            COALESCE(MI.QTD_MOV_ATE_INICIO, 0) AS bridge_quantity,
            COALESCE(MI.VALOR_MOV_ATE_INICIO, 0) AS bridge_value,
            COALESCE(MP.QTD_MOV_LIQ_PERIODO, 0) AS period_net_quantity,
            COALESCE(MP.VALOR_MOV_LIQ_PERIODO, 0) AS period_net_value,
            COALESCE(FB.QTD_FECHAMENTO_BASE, 0)
                + COALESCE(MI.QTD_MOV_ATE_INICIO, 0)
                + COALESCE(MP.QTD_MOV_LIQ_PERIODO, 0) AS total_stock_quantity,
            COALESCE(FB.VALOR_FECHAMENTO_BASE, 0)
                + COALESCE(MI.VALOR_MOV_ATE_INICIO, 0)
                + COALESCE(MP.VALOR_MOV_LIQ_PERIODO, 0) AS total_stock_value
        FROM fechamento_base FB
        FULL OUTER JOIN mov_entre_base_e_inicio MI
            ON MI.FILIAL = FB.FILIAL
        FULL OUTER JOIN mov_periodo MP
            ON MP.FILIAL = COALESCE(FB.FILIAL, MI.FILIAL)
        ORDER BY COALESCE(FB.FILIAL, MI.FILIAL, MP.FILIAL)
    """

    def _uses_historical_estimation(self, request: GetStockValueRequest) -> bool:
        return request.uses_historical_estimation

    def _resolve_historical_period(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, str]:
        qb = QueryBuilder()
        period_start = qb.convert_date_to_protheus(request.start_date)
        period_end = qb.convert_date_to_protheus(request.end_date)

        if not period_start or not period_end:
            raise ValueError(
                "Para consultar estoque em uma data passada, informe start_date e end_date válidos."
            )

        end_date = datetime.strptime(period_end, "%Y%m%d").date()
        period_end_exclusive = (end_date + timedelta(days=1)).strftime("%Y%m%d")
        return period_start, period_end_exclusive

    def _branch_filter_clause(self, column: str, branch: str | None) -> tuple[str, tuple]:
        if branch:
            return f" AND {column} = ?", (branch,)
        return "", ()

    def _build_historical_query(self, request: GetStockValueRequest) -> tuple[str, tuple]:
        period_start, period_end_exclusive = self._resolve_historical_period(request)
        branch = request.branch

        sb9_filter, sb9_params = self._branch_filter_clause("B9_FILIAL", branch)
        sb9_b9_filter, sb9_b9_params = self._branch_filter_clause("B9.B9_FILIAL", branch)
        d3_filter, d3_params = self._branch_filter_clause("D3.D3_FILIAL", branch)

        sql = self._HISTORICAL_STOCK_SQL.format(
            sb9_branch_filter=sb9_filter,
            sb9_branch_filter_b9=sb9_b9_filter,
            d3_branch_filter=d3_filter,
        )

        params = (
            (period_start,)
            + sb9_params
            + sb9_b9_params
            + (period_start,)
            + d3_params
            + (period_start, period_end_exclusive)
            + d3_params
        )
        return sql, params

    def _get_historical_rows(self, request: GetStockValueRequest) -> list[dict]:
        sql, params = self._build_historical_query(request)

        with self as repo:
            return repo.execute_query(sql, params) or []

    def _build_filters(self, request: GetStockValueRequest):
        qb = QueryBuilder()
        qb.raw("SB2.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("SB2.B2_FILIAL", request.branch)

        if request.location:
            qb.eq("SB2.B2_LOCAL", request.location)

        return qb.build()

    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
        if self._uses_historical_estimation(request):
            rows = self._get_historical_rows(request)
            branch_label = request.branch or "consolidated"
            location_label = request.location or "all"

            total_stock_value = sum(float(row.get("total_stock_value") or 0) for row in rows)
            total_stock_quantity = sum(
                float(row.get("total_stock_quantity") or 0) for row in rows
            )

            return {
                "branch": branch_label,
                "location": location_label,
                "total_stock_value": total_stock_value,
                "total_stock_quantity": total_stock_quantity,
                "total_records": len(rows),
                "total_products": 0,
                "total_locations": 0,
            }

        where_clause, params = self._build_filters(request)

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

    def get_stock_value_by_branch(self, request: GetStockValueRequest) -> list[dict]:
        if self._uses_historical_estimation(request):
            rows = self._get_historical_rows(request)
            return [
                {
                    "branch": row.get("branch"),
                    "total_stock_value": float(row.get("total_stock_value") or 0),
                    "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                    "total_records": 1,
                    "total_products": 0,
                    "total_locations": 0,
                    "closing_base_date": row.get("closing_base_date"),
                    "closing_base_value": float(row.get("closing_base_value") or 0),
                    "closing_base_quantity": float(row.get("closing_base_quantity") or 0),
                    "bridge_value": float(row.get("bridge_value") or 0),
                    "period_net_value": float(row.get("period_net_value") or 0),
                }
                for row in rows
            ]

        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                SB2.B2_FILIAL AS branch,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SB2.B2_COD) AS total_products,
                COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
            FROM SB2010 SB2
            WHERE {where_clause}
            GROUP BY SB2.B2_FILIAL
            ORDER BY SB2.B2_FILIAL
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_stock_value_by_location(self, request: GetStockValueRequest) -> list[dict]:
        if self._uses_historical_estimation(request):
            return []

        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                SB2.B2_FILIAL AS branch,
                SB2.B2_LOCAL AS location,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SB2.B2_COD) AS total_products
            FROM SB2010 SB2
            WHERE {where_clause}
            GROUP BY SB2.B2_FILIAL, SB2.B2_LOCAL
            ORDER BY SB2.B2_FILIAL, SB2.B2_LOCAL
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_top_products_by_stock_value(self, request: GetStockValueRequest) -> list[dict]:
        if self._uses_historical_estimation(request):
            return []

        where_clause, params = self._build_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 10) or 10))

        sql = f"""
            SELECT TOP {limit}
                SB2.B2_COD AS product_code,
                MAX(SB1.B1_DESC) AS product_description,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                ROUND(AVG(CAST(SB2.B2_CM1 AS DECIMAL(18, 6))), 6) AS average_unit_cost,
                COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
            FROM SB2010 SB2
            LEFT JOIN SB1010 SB1
                ON SB1.D_E_L_E_T_ = ''
               AND SB1.B1_COD = SB2.B2_COD
            WHERE {where_clause}
            GROUP BY SB2.B2_COD
            ORDER BY total_stock_value DESC, product_code
        """

        with self as repo:
            return repo.execute_query(sql, params) or []
