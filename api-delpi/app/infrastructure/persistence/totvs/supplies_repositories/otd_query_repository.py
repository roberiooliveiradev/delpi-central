from __future__ import annotations

from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.domain.ports.supplies.otd_query_repository_port import OtdQueryRepositoryPort
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_RAW_MATERIAL,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.supplies_repositories.otd_physical_receipts import (
    resolve_physical_source,
)

_DETAIL_VIEW = "VW_PONTUALIDADE_FORNECEDORES"


class OtdQueryRepository(BaseRepository, OtdQueryRepositoryPort):
    """OTD compras — universo MP OU prefixo de código (ver protheus_product_types)."""

    @staticmethod
    def _product_universe_clause(*, table_alias: str | None = None) -> tuple[str, tuple]:
        prefix = f"{table_alias}." if table_alias else ""
        clause = (
            f"("
            f"RTRIM(LTRIM({prefix}TIPO_PRODUTO)) = ?"
            f" OR LEFT(RTRIM(LTRIM({prefix}PRODUTO)), {SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN}) = ?"
            f")"
        )
        params = (PRODUCT_TYPE_RAW_MATERIAL, SUPPLIES_OTD_PRODUCT_CODE_PREFIX)
        return clause, params

    def _source(self, request: GetOTDRequest) -> tuple[str, str, tuple, bool]:
        physical = resolve_physical_source(
            self,
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        if physical is None:
            return "", f"{_DETAIL_VIEW} WITH (NOLOCK)", (), False
        return "WITH " + physical.cte, "OTD_EFFECTIVE", physical.params, True

    def _build_details_filters(self, request: GetOTDRequest) -> tuple[str, tuple]:
        qb = QueryBuilder()

        if request.branch:
            qb.eq("FILIAL", request.branch)

        qb.date_range("DT_DIGITACAO", request.start_date, request.end_date)

        where_clause, params = qb.build()
        universe_clause, universe_params = self._product_universe_clause()

        if where_clause and where_clause.strip().upper() != "1=1":
            combined = f"({where_clause}) AND {universe_clause}"
        else:
            combined = universe_clause

        return combined, tuple(params) + universe_params

    def get_otd_summary(self, request: GetOTDRequest) -> dict:
        where_clause, params = self._build_details_filters(request)
        source_prefix, source_table, source_params, has_physical = self._source(request)
        branch_label = request.branch or "consolidated"

        sql = f"""{source_prefix}
            SELECT
                ? AS branch,
                ISNULL(MIN(CONVERT(VARCHAR(10), DT_DIGITACAO, 23)), '') AS start_date,
                ISNULL(MAX(CONVERT(VARCHAR(10), DT_DIGITACAO, 23)), '') AS end_date,
                ISNULL(COUNT(*), 0) AS total_lines,
                ISNULL(SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END), 0) AS on_time_lines,
                ISNULL(SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END), 0) AS late_lines,
                CASE
                    WHEN ISNULL(COUNT(*), 0) = 0 THEN 0
                    ELSE ROUND(
                        (
                            ISNULL(SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END), 0) * 100.0
                        ) / NULLIF(COUNT(*), 0),
                        2
                    )
                END AS otd_percentage
            FROM {source_table}
            WHERE {where_clause}
        """

        final_params = source_params + (branch_label,) + params

        with self as repo:
            result = repo.execute_one(sql, final_params)

        return result or {
            "branch": branch_label,
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "total_lines": 0,
            "on_time_lines": 0,
            "late_lines": 0,
            "otd_percentage": 0,
        }

    def get_otd_monthly_breakdown(self, request: GetOTDRequest) -> list[dict]:
        where_clause, params = self._build_details_filters(request)
        source_prefix, source_table, source_params, has_physical = self._source(request)

        sql = f"""{source_prefix}
            SELECT
                FILIAL AS branch,
                YEAR(DT_DIGITACAO) AS year,
                MONTH(DT_DIGITACAO) AS month,
                CONVERT(
                    VARCHAR(10),
                    DATEFROMPARTS(YEAR(DT_DIGITACAO), MONTH(DT_DIGITACAO), 1),
                    23
                ) AS month_date,
                COUNT(*) AS total_lines,
                SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) AS on_time_lines,
                SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END) AS late_lines,
                ROUND(
                    (
                        SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) * 100.0
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS otd_percentage
            FROM {source_table}
            WHERE {where_clause}
            GROUP BY
                FILIAL,
                YEAR(DT_DIGITACAO),
                MONTH(DT_DIGITACAO)
            ORDER BY year DESC, month DESC, FILIAL
        """

        with self as repo:
            return repo.execute_query(sql, source_params + params) or []

    def get_top_late_suppliers(self, request: GetOTDRequest) -> list[dict]:
        where_clause, params = self._build_details_filters(request)
        source_prefix, source_table, source_params, has_physical = self._source(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""{source_prefix}
            SELECT TOP {limit}
                FORNECEDOR AS supplier_code,
                LOJA AS supplier_store,
                MAX(NOME_FORNECEDOR) AS supplier_name,
                COUNT(*) AS total_lines,
                SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) AS on_time_lines,
                SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END) AS late_lines,
                ROUND(AVG(CAST(DIAS AS DECIMAL(18, 2))), 2) AS average_days_diff,
                ROUND(
                    (
                        SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) * 100.0
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) AS otd_percentage
            FROM {source_table}
            WHERE {where_clause}
            GROUP BY FORNECEDOR, LOJA
            HAVING SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END) > 0
            ORDER BY late_lines DESC, average_days_diff ASC, supplier_code
        """

        with self as repo:
            return repo.execute_query(sql, source_params + params) or []

    def get_late_deliveries(self, request: GetOTDRequest) -> list[dict]:
        where_clause, params = self._build_details_filters(request)
        source_prefix, source_table, source_params, has_physical = self._source(request)
        limit = max(1, int(getattr(request, "details_limit", 20) or 20))
        original_entry = "DT_DIGITACAO_ERP" if has_physical else "DT_DIGITACAO"
        receipt_origin = "RECEIPT_SOURCE" if has_physical else "'erp_digitacao'"

        sql = f"""{source_prefix}
            SELECT TOP {limit}
                FILIAL AS branch,
                FORNECEDOR AS supplier_code,
                LOJA AS supplier_store,
                NOME_FORNECEDOR AS supplier_name,
                DOCUMENTO AS document,
                NUMERO_PEDIDO AS order_number,
                ITEM_PEDIDO AS order_item,
                PRODUTO AS product_code,
                DESCRICAO_PRODUTO AS product_description,
                TIPO_PRODUTO AS product_type,
                QUANTIDADE AS quantity,
                CONVERT(VARCHAR(10), DT_EMISSAO_PC, 23) AS purchase_order_issue_date,
                CONVERT(VARCHAR(10), DT_ENTREGA, 23) AS expected_delivery_date,
                CONVERT(VARCHAR(10), {original_entry}, 23) AS receipt_entry_date,
                CONVERT(VARCHAR(10), DT_DIGITACAO, 23) AS receipt_effective_date,
                {receipt_origin} AS receipt_source,
                CONVERT(VARCHAR(10), DT_EMISSAO_NF, 23) AS invoice_issue_date,
                DIAS AS days_diff
            FROM {source_table}
            WHERE {where_clause}
              AND DIAS < 0
            ORDER BY DT_ENTREGA DESC, DIAS ASC, FORNECEDOR, NUMERO_PEDIDO, ITEM_PEDIDO
        """

        with self as repo:
            return repo.execute_query(sql, source_params + params) or []
