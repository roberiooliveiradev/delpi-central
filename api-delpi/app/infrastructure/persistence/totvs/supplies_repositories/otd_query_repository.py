from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.domain.ports.supplies.otd_query_repository_port import OtdQueryRepositoryPort


class OtdQueryRepository(BaseRepository, OtdQueryRepositoryPort):

    def _build_monthly_filters(self, request: GetOTDRequest):
        qb = QueryBuilder()

        if request.branch:
            qb.eq("FILIAL", request.branch)

        qb.date_range("MES_ANO", request.start_date, request.end_date)

        return qb.build()

    def _build_details_filters(self, request: GetOTDRequest):
        qb = QueryBuilder()

        if request.branch:
            qb.eq("FILIAL", request.branch)

        qb.date_range("DT_DIGITACAO", request.start_date, request.end_date)

        return qb.build()

    def get_otd_summary(self, request: GetOTDRequest) -> dict:
        where_clause, params = self._build_monthly_filters(request)

        sql = f"""
            SELECT
                ? AS branch,
                ISNULL(MIN(CONVERT(VARCHAR(10), MES_ANO, 23)), '') AS start_date,
                ISNULL(MAX(CONVERT(VARCHAR(10), MES_ANO, 23)), '') AS end_date,
                ISNULL(SUM(TOTAL_LINHAS), 0) AS total_lines,
                ISNULL(SUM(LINHAS_NO_PRAZO), 0) AS on_time_lines,
                ISNULL(SUM(LINHAS_EM_ATRASO), 0) AS late_lines,
                CASE
                    WHEN ISNULL(SUM(TOTAL_LINHAS), 0) = 0 THEN 0
                    ELSE ROUND(
                        (ISNULL(SUM(LINHAS_NO_PRAZO), 0) * 100.0) / NULLIF(SUM(TOTAL_LINHAS), 0),
                        2
                    )
                END AS otd_percentage
            FROM VW_PONTUALIDADE_FORNECEDORES_MENSAL
            WHERE {where_clause}
        """

        branch_label = request.branch or "consolidated"
        final_params = (branch_label,) + params

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
        where_clause, params = self._build_monthly_filters(request)

        sql = f"""
            SELECT
                FILIAL AS branch,
                ANO AS year,
                MES AS month,
                CONVERT(VARCHAR(10), MES_ANO, 23) AS month_date,
                TOTAL_LINHAS AS total_lines,
                LINHAS_NO_PRAZO AS on_time_lines,
                LINHAS_EM_ATRASO AS late_lines,
                PERCENTUAL_ATENDIMENTO AS otd_percentage
            FROM VW_PONTUALIDADE_FORNECEDORES_MENSAL
            WHERE {where_clause}
            ORDER BY ANO DESC, MES DESC, FILIAL
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_top_late_suppliers(self, request: GetOTDRequest) -> list[dict]:
        where_clause, params = self._build_details_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""
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
            FROM VW_PONTUALIDADE_FORNECEDORES
            WHERE {where_clause}
            GROUP BY FORNECEDOR, LOJA
            HAVING SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END) > 0
            ORDER BY late_lines DESC, average_days_diff ASC, supplier_code
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_late_deliveries(self, request: GetOTDRequest) -> list[dict]:
        where_clause, params = self._build_details_filters(request)
        limit = max(1, int(getattr(request, "details_limit", 20) or 20))

        sql = f"""
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
                CONVERT(VARCHAR(10), DT_DIGITACAO, 23) AS receipt_entry_date,
                CONVERT(VARCHAR(10), DT_EMISSAO_NF, 23) AS invoice_issue_date,
                DIAS AS days_diff
            FROM VW_PONTUALIDADE_FORNECEDORES
            WHERE {where_clause}
              AND DIAS < 0
            ORDER BY DT_ENTREGA DESC, DIAS ASC, FORNECEDOR, NUMERO_PEDIDO, ITEM_PEDIDO
        """

        with self as repo:
            return repo.execute_query(sql, params) or []