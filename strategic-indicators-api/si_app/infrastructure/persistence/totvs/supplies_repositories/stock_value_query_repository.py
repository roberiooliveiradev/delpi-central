from datetime import datetime, timedelta

from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from si_app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)
from si_app.shared.branch_filter import effective_query_branch
from si_app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
    HISTORICAL_STOCK_BY_BRANCH_SQL,
    HISTORICAL_STOCK_BY_LOCATION_SQL,
    HISTORICAL_STOCK_SUMMARY_SQL,
    HISTORICAL_STOCK_TOP_PRODUCTS_SQL,
)


class StockValueQueryRepository(BaseRepository, StockValueQueryRepositoryPort):

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

    def _location_filter_clause(self, column: str, location: str | None) -> tuple[str, tuple]:
        normalized = (location or "").strip()
        if normalized:
            return f" AND RTRIM({column}) = ?", (normalized,)
        return "", ()

    def _format_historical_sql(self, template: str, request: GetStockValueRequest) -> tuple[str, tuple]:
        period_start, period_end_exclusive = self._resolve_historical_period(request)
        branch = effective_query_branch(request.branch)
        location = (request.location or "").strip() or None

        sb9_filter, sb9_params = self._branch_filter_clause("B9_FILIAL", branch)
        sb9_b9_filter, sb9_b9_params = self._branch_filter_clause("B9.B9_FILIAL", branch)
        sb9_loc_filter, sb9_loc_params = self._location_filter_clause("B9.B9_LOCAL", location)
        d3_filter, d3_params = self._branch_filter_clause("D3.D3_FILIAL", branch)
        d3_loc_filter, d3_loc_params = self._location_filter_clause("D3.D3_LOCAL", location)

        sql = template.format(
            sb9_branch_filter=sb9_filter,
            sb9_branch_filter_b9=sb9_b9_filter,
            sb9_location_filter=sb9_loc_filter,
            d3_branch_filter=d3_filter,
            d3_location_filter=d3_loc_filter,
            limit=max(1, int(getattr(request, "top_limit", 10) or 10)),
        )

        params = (
            (period_start,)
            + sb9_params
            + sb9_b9_params
            + sb9_loc_params
            + (period_start,)
            + d3_params
            + d3_loc_params
            + (period_start, period_end_exclusive)
            + d3_params
            + d3_loc_params
        )
        return sql, params

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
        if self._uses_historical_estimation(request):
            sql, params = self._format_historical_sql(HISTORICAL_STOCK_SUMMARY_SQL, request)
            branch_label = request.branch or "consolidated"
            location_label = request.location or "all"

            with self as repo:
                result = repo.execute_one(sql, params)

            result = result or {}
            return {
                "branch": branch_label,
                "location": location_label,
                "total_stock_value": float(result.get("total_stock_value") or 0),
                "total_stock_quantity": float(result.get("total_stock_quantity") or 0),
                "total_records": int(result.get("total_records") or 0),
                "total_products": int(result.get("total_products") or 0),
                "total_locations": int(result.get("total_locations") or 0),
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
            sql, params = self._format_historical_sql(HISTORICAL_STOCK_BY_BRANCH_SQL, request)

            with self as repo:
                rows = repo.execute_query(sql, params) or []

            return [
                {
                    "branch": row.get("branch"),
                    "total_stock_value": float(row.get("total_stock_value") or 0),
                    "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                    "total_records": int(row.get("total_records") or 0),
                    "total_products": int(row.get("total_products") or 0),
                    "total_locations": int(row.get("total_locations") or 0),
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
            sql, params = self._format_historical_sql(
                HISTORICAL_STOCK_BY_LOCATION_SQL,
                request,
            )

            with self as repo:
                rows = repo.execute_query(sql, params) or []

            return [
                {
                    "branch": row.get("branch"),
                    "location": row.get("location"),
                    "total_stock_value": float(row.get("total_stock_value") or 0),
                    "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                    "total_records": int(row.get("total_records") or 0),
                    "total_products": int(row.get("total_products") or 0),
                }
                for row in rows
                if float(row.get("total_stock_value") or 0) != 0
                or float(row.get("total_stock_quantity") or 0) != 0
            ]

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
            sql, params = self._format_historical_sql(
                HISTORICAL_STOCK_TOP_PRODUCTS_SQL,
                request,
            )

            with self as repo:
                rows = repo.execute_query(sql, params) or []

            return [
                {
                    "product_code": row.get("product_code"),
                    "product_description": row.get("product_description"),
                    "total_stock_value": float(row.get("total_stock_value") or 0),
                    "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                    "average_unit_cost": 0,
                    "total_locations": int(row.get("total_locations") or 0),
                }
                for row in rows
            ]

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
