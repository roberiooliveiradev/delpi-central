from datetime import datetime, timedelta

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_cache import (
    get_cached_stock_value_bundle,
    set_cached_stock_value_bundle,
    stock_value_cache_key,
)
from app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
    HISTORICAL_STOCK_BUNDLE_BATCH_SQL,
    HISTORICAL_STOCK_BUNDLE_SUMMARY_ONLY_BATCH_SQL,
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

    def _format_historical_bundle_sql(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, tuple]:
        period_start, period_end_exclusive = self._resolve_historical_period(request)
        branch = request.branch
        location = (request.location or "").strip() or None

        sb9_filter, sb9_params = self._branch_filter_clause("B9_FILIAL", branch)
        sb9_b9_filter, sb9_b9_params = self._branch_filter_clause("B9.B9_FILIAL", branch)
        sb9_loc_filter, sb9_loc_params = self._location_filter_clause("B9.B9_LOCAL", location)
        d3_filter, d3_params = self._branch_filter_clause("D3.D3_FILIAL", branch)
        d3_loc_filter, d3_loc_params = self._location_filter_clause("D3.D3_LOCAL", location)

        template = (
            HISTORICAL_STOCK_BUNDLE_SUMMARY_ONLY_BATCH_SQL
            if request.summary_only
            else HISTORICAL_STOCK_BUNDLE_BATCH_SQL
        )
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

        if request.branch:
            qb.eq("SB2.B2_FILIAL", request.branch)

        if request.location:
            qb.eq("SB2.B2_LOCAL", request.location)

        return qb.build()

    def _labels(self, request: GetStockValueRequest) -> tuple[str, str]:
        return request.branch or "consolidated", request.location or "all"

    def _normalize_summary_row(
        self,
        row: dict | None,
        *,
        branch_label: str,
        location_label: str,
    ) -> dict:
        row = row or {}
        return {
            "branch": branch_label,
            "location": location_label,
            "total_stock_value": float(row.get("total_stock_value") or 0),
            "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
            "total_records": int(row.get("total_records") or 0),
            "total_products": int(row.get("total_products") or 0),
            "total_locations": int(row.get("total_locations") or 0),
        }

    def _normalize_branch_rows(self, rows: list[dict]) -> list[dict]:
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

    def _normalize_location_rows(self, rows: list[dict]) -> list[dict]:
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

    def _normalize_top_product_rows(self, rows: list[dict]) -> list[dict]:
        return [
            {
                "product_code": row.get("product_code"),
                "product_description": row.get("product_description"),
                "total_stock_value": float(row.get("total_stock_value") or 0),
                "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                "average_unit_cost": float(row.get("average_unit_cost") or 0),
                "total_locations": int(row.get("total_locations") or 0),
            }
            for row in rows
        ]

    def _bundle_from_resultsets(
        self,
        resultsets: list[dict],
        *,
        branch_label: str,
        location_label: str,
    ) -> dict:
        datasets = [item.get("data") or [] for item in resultsets]
        summary_row = datasets[0][0] if datasets and datasets[0] else {}
        by_branch_rows = datasets[1] if len(datasets) > 1 else []
        by_location_rows = datasets[2] if len(datasets) > 2 else []
        top_product_rows = datasets[3] if len(datasets) > 3 else []

        return {
            "summary": self._normalize_summary_row(
                summary_row,
                branch_label=branch_label,
                location_label=location_label,
            ),
            "by_branch": self._normalize_branch_rows(by_branch_rows),
            "by_location": self._normalize_location_rows(by_location_rows),
            "top_products": self._normalize_top_product_rows(top_product_rows),
        }

    def _fetch_historical_bundle(self, request: GetStockValueRequest) -> dict:
        sql, params = self._format_historical_bundle_sql(request)
        branch_label, location_label = self._labels(request)

        with self as repo:
            resultsets = repo.execute_query_multiple(sql, params)

        return self._bundle_from_resultsets(
            resultsets,
            branch_label=branch_label,
            location_label=location_label,
        )

    def _fetch_current_bundle(self, request: GetStockValueRequest) -> dict:
        where_clause, params = self._build_filters(request)
        branch_label, location_label = self._labels(request)
        limit = max(1, int(getattr(request, "top_limit", 10) or 10))

        summary_sql = f"""
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

        if request.summary_only:
            sql = summary_sql
        else:
            sql = f"""
                {summary_sql};

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
                ORDER BY SB2.B2_FILIAL;

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
                ORDER BY SB2.B2_FILIAL, SB2.B2_LOCAL;

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
                ORDER BY total_stock_value DESC, product_code;
            """

        final_params = (branch_label, location_label) + params

        with self as repo:
            resultsets = repo.execute_query_multiple(sql, final_params)

        return self._bundle_from_resultsets(
            resultsets,
            branch_label=branch_label,
            location_label=location_label,
        )

    def get_stock_value_bundle(self, request: GetStockValueRequest) -> dict:
        cache_key = stock_value_cache_key(request)
        cached = get_cached_stock_value_bundle(cache_key)
        if cached is not None:
            return cached

        if self._uses_historical_estimation(request):
            bundle = self._fetch_historical_bundle(request)
        else:
            bundle = self._fetch_current_bundle(request)

        set_cached_stock_value_bundle(cache_key, bundle)
        return bundle

    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
        return self.get_stock_value_bundle(request)["summary"]

    def get_stock_value_by_branch(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["by_branch"]

    def get_stock_value_by_location(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["by_location"]

    def get_top_products_by_stock_value(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["top_products"]
