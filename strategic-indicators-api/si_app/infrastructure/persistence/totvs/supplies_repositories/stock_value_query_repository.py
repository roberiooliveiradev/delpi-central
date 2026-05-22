from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from si_app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)
from si_app.shared.branch_filter import effective_query_branch


class StockValueQueryRepository(BaseRepository, StockValueQueryRepositoryPort):

    def _build_filters(self, request: GetStockValueRequest):
        qb = QueryBuilder()
        qb.raw("SB2.D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("SB2.B2_FILIAL", branch)

        if request.location:
            qb.eq("SB2.B2_LOCAL", request.location)

        return qb.build()

    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
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